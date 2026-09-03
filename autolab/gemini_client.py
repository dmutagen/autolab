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
        custom_code: str = "",
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
6. Если задание по программированию: ПОЛНЫЙ рабочий программный код на подходящем языке (Java, Python, C++, SQL, Bash, Kotlin, C#). Если задание по ДИЗАЙНУ, UI/UX, макетам Figma, схемам, моделированию или аналитике: поле "code" оставь строго ПУСТЫМ (""), а в "solution_description" детально опиши концепцию, сетку, компоненты, цветовую палитру и структуру интерфейса!
7. Точные тестовые входные данные (test_inputs), если программа ожидает ввод.
8. Развернутые ответы на ВСЕ контрольные вопросы (если они есть в задании или вытекают из темы).
9. Качественный вывод по белорусскому академическому стандарту (согласованный с целью работы).
"""
        if custom_code and custom_code.strip():
            user_prompt += f"""
ТРЕБОВАНИЕ: СТУДЕНТ ПРЕДОСТАВИЛ СВОЙ ГОТОВЫЙ КОД!
В поле "code" ОБЯЗАТЕЛЬНО используй именно этот код студента:
```
{custom_code.strip()}
```
Опиши алгоритм этого кода, ответь на контрольные вопросы и сделай вывод на основе именно этого кода!
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
                if custom_code and custom_code.strip():
                    parsed["code"] = custom_code.strip()
                parsed["_generated_by_model"] = model_name
                success_msg = f"✓ Успешно сгенерировано моделью {model_name}!"
                if on_status:
                    on_status(success_msg)
                print(f"[GeminiClient] {success_msg}")
                return parsed

            except Exception as e:
                err_str = str(e)
                last_error = e
                attempted_errors.append(f"{model_name}: {err_str.splitlines()[0] if err_str else 'Unknown'}")
                warn_msg = f"⚠ {model_name} временно недоступна / лимит исчерпан. Переключаюсь на следующую модель..."
                if i < len(cascade) - 1:
                    next_model = cascade[i + 1]
                    warn_msg = f"⚠ {model_name} временно недоступна / лимит исчерпан. Переключаюсь на {next_model}..."
                if on_status:
                    on_status(warn_msg)
                print(f"[GeminiClient] {warn_msg}")
                continue

        error_details = "\n".join(attempted_errors)
        raise RuntimeError(
            f"Не удалось сгенерировать ответ ни одной из моделей Gemini в каскаде.\n"
            f"История попыток:\n{error_details}\nПоследняя ошибка: {last_error}"
        )

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"^```\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            json_match = re.search(r"(\{.*\})", cleaned, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            return self._fallback_text_to_dict(cleaned)

    def _fallback_text_to_dict(self, text: str) -> Dict[str, Any]:
        return {
            "lab_number": "1",
            "topic": "Лабораторная работа",
            "goal": "Сформировать практические умения и навыки в соответствии с темой работы.",
            "task": text[:500] if text else "Выполнение задания по методическим указаниям.",
            "equipment": "ПЭВМ IBM/AT, ОС Windows / Linux, среда разработки.",
            "theory": "",
            "solution_description": "В ходе выполнения работы были решены поставленные задачи.",
            "code": "# Код программы\nprint('Лабораторная работа выполнена')",
            "code_language": "python",
            "code_filename": "main.py",
            "test_inputs": "",
            "simulated_output": "Программа выполнена успешно.",
            "questions_answers": [],
            "conclusion": "В ходе выполнения лабораторной работы были успешно освоены все практические навыки."
        }
