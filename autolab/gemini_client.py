import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from google import genai
from google.genai import types
from PIL import Image

from autolab.config import AppConfig, MODELS_CASCADE
from autolab.knowledge import KnowledgeManager

class GeminiLabClient:
    def __init__(self, config: AppConfig):
        self.config = config
        self.km = KnowledgeManager()

    def generate_lab_solution(
        self,
        task_text: str,
        subject: str = "",
        variant: str = "",
        image_paths: Optional[List[Path]] = None,
        custom_instructions: str = "",
        on_status: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        api_key = self.config.gemini_api_key.strip()
        if not api_key:
            raise ValueError("GEMINI_API_KEY не установлен. Пожалуйста, укажите ваш бесплатный ключ Gemini API в настройках или файле config.json.")

        client = genai.Client(api_key=api_key)
        system_instruction = self.km.build_system_prompt(subject=subject)

        # Build prompt parts
        prompt_parts = []
        user_prompt = f"""ВЫПОЛНИ ЛАБОРАТОРНУЮ / ПРАКТИЧЕСКУЮ РАБОТУ.

ПРЕДМЕТ: {subject or 'Информационные технологии / Программирование'}
ВАРИАНТ: {variant or 'согласно заданию'}
ДОПОЛНИТЕЛЬНЫЕ УКАЗАНИЯ: {custom_instructions or 'Соблюдай все стандарты оформления'}

ИСХОДНОЕ ЗАДАНИЕ / МЕТОДИЧКА:
{task_text}

СФОРМИРУЙ ПОЛНЫЙ JSON ПО ЗАДАННОМУ ФОРМАТУ.
Обязательно включи:
1. Номер работы и точную тему.
2. Цель работы.
3. Полный текст задания.
4. Оснащение работы.
5. Краткие теоретические сведения и подробное описание хода работы.
6. ПОЛНЫЙ, рабочий программный код на подходящем языке программирования (Java, Python, C++, SQL, Bash, Kotlin, C#). Код должен компилироваться и выполняться без ошибок!
7. Точные тестовые входные данные (test_inputs), если программа ожидает ввод.
8. Развернутые ответы на ВСЕ контрольные вопросы (если они есть в задании или вытекают из темы).
9. Качественный вывод по белорусскому академическому стандарту (согласованный с целью работы).
"""
        prompt_parts.append(user_prompt)

        # Attach images if any (multimodal)
        if image_paths:
            for p in image_paths:
                if p.exists():
                    try:
                        img = Image.open(str(p))
                        prompt_parts.append(img)
                    except Exception as e:
                        print(f"Warning: Failed to load image {p}: {e}")

        # Build model cascade starting with the freshest preferred model
        preferred = self.config.model_name or MODELS_CASCADE[0]
        cascade = [preferred] + [m for m in MODELS_CASCADE if m != preferred]

        last_error = None
        attempted_errors = []

        for i, model_name in enumerate(cascade):
            status_msg = f"Попытка генерации через {model_name}..."
            if on_status:
                on_status(status_msg)
            print(f"[GeminiClient] {status_msg}")

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt_parts,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        response_mime_type="application/json",
                        temperature=0.2
                    )
                )
                raw_text = response.text or ""
                parsed = self._parse_json_response(raw_text)
                parsed["_generated_by_model"] = model_name
                success_msg = f"✓ Успешно сгенерировано моделью {model_name}!"
                if on_status:
                    on_status(success_msg)
                print(f"[GeminiClient] {success_msg}")
                return parsed

            except Exception as e:
                err_str = str(e)
                attempted_errors.append(f"{model_name}: {err_str[:120]}")
                last_error = e

                # Check if this error warrants fallback to next model
                is_quota = any(kw in err_str for kw in ["RESOURCE_EXHAUSTED", "429", "quota", "limit"])
                is_unavailable = any(kw in err_str for kw in ["503", "UNAVAILABLE", "high demand"])
                is_not_found = any(kw in err_str for kw in ["404", "NOT_FOUND", "not found", "no longer available"])

                if i < len(cascade) - 1:
                    next_model = cascade[i + 1]
                    fallback_msg = f"⚠ {model_name} временно недоступна / лимит исчерпан. Переключаюсь на {next_model}..."
                    if on_status:
                        on_status(fallback_msg)
                    print(f"[GeminiClient] {fallback_msg}")
                    continue
                else:
                    break

        all_errs = "\n".join(attempted_errors)
        raise RuntimeError(f"Все модели Gemini в цепочке вернули ошибку:\n{all_errs}")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        text = text.strip()
        if text.startswith("```json"):
            text = text[7:]
        elif text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

        try:
            return json.loads(text)
        except Exception:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError("Не удалось распарсить JSON-ответ от Gemini:\n" + text[:400])
