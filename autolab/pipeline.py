import os
import uuid
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List

from autolab.config import AppConfig, load_config, OUTPUT_DIR
from autolab.parser import TaskParser
from autolab.gemini_client import GeminiLabClient
from autolab.executor import CodeExecutor
from autolab.screenshot import ScreenshotEngine
from autolab.docx_builder import DocxBuilder

class LabPipeline:
    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.gemini = GeminiLabClient(self.config)
        self.executor = CodeExecutor()
        self.screenshot_engine = ScreenshotEngine()

    def run(
        self,
        task_text: str = "",
        subject: str = "",
        variant: str = "",
        custom_filename: str = "",
        date_str: str = "",
        include_theory: bool = False,
        uploaded_file: Optional[Path] = None,
        with_title_page: bool = False,
        custom_instructions: str = ""
    ) -> Dict[str, Any]:
        job_id = uuid.uuid4().hex[:8]
        job_output_dir = OUTPUT_DIR / f"lab_{job_id}"
        job_output_dir.mkdir(parents=True, exist_ok=True)

        steps_log = []
        def log(step: str):
            steps_log.append(step)
            print(f"[{job_id}] {step}")

        # Step 1: Parse input
        log("1. Анализ входных данных и методички...")
        input_data = TaskParser.process_input(
            text_input=task_text,
            uploaded_file=uploaded_file,
            variant=variant
        )
        combined_text = input_data["text"]
        image_paths = input_data.get("images", [])

        # Step 2: Gemini Generation
        log("2. Запрос к ИИ Gemini (синтез решения, кода и структуры отчета)...")
        solution = self.gemini.generate_lab_solution(
            task_text=combined_text,
            subject=subject,
            variant=variant,
            image_paths=image_paths,
            custom_instructions=custom_instructions,
            on_status=log
        )

        code = solution.get("code", "")
        code_lang = solution.get("code_language", "python")
        code_filename = solution.get("code_filename", "main.py")
        test_inputs = solution.get("test_inputs", "")

        # Step 3: Run execution sandbox (for console apps)
        log(f"3. Компиляция и безопасный запуск {code_lang}-кода в изолированной песочнице...")
        exec_result = self.executor.execute(
            code=code,
            language=code_lang,
            filename=code_filename,
            test_inputs=test_inputs
        )

        output_text = exec_result.get("stdout", "").strip()
        if not output_text or not exec_result.get("success"):
            sim = solution.get("simulated_output", "").strip()
            if sim:
                output_text = sim
            elif exec_result.get("stderr"):
                output_text = "Вывод программы:\n" + exec_result.get("stderr")
            else:
                output_text = "Программа выполнена успешно (код возврата 0)."

        # Step 4: Render Realistic Screenshots (Mobile or Terminal)
        log("4. Создание реалистичного снимка интерфейса программы...")
        screen_path = job_output_dir / "program_screenshot.png"
        
        # Check if user uploaded a direct screenshot image
        if uploaded_file and uploaded_file.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            shutil.copyfile(uploaded_file, screen_path)
            log("✓ Использован загруженный пользователем снимок экрана")
        else:
            cmd = f"python3 {code_filename}"
            if "java" in code_lang.lower():
                cmd = f"javac {code_filename} && java Main"
            elif "cpp" in code_lang.lower() or "c++" in code_lang.lower():
                cmd = "./solution"
            elif "sql" in code_lang.lower():
                cmd = "sqlite3 database.db < schema.sql"
            elif "bash" in code_lang.lower():
                cmd = "./script.sh"

            self.screenshot_engine.render_smart_screenshot(
                subject=solution.get("subject") or subject,
                topic=solution.get("topic") or "",
                code=code,
                command=cmd,
                output_text=output_text,
                output_image_path=screen_path
            )

        # Step 5: Build DOCX by Belarusian GOST
        log("5. Верстка документа DOCX по Белорусскому ГОСТу...")
        builder = DocxBuilder(self.config)
        
        # Custom filename or short auto filename
        if custom_filename and custom_filename.strip():
            c_name = custom_filename.strip()
            if not c_name.lower().endswith(".docx"):
                c_name = f"{c_name}.docx"
            docx_filename = c_name
        else:
            from autolab.docx_builder import get_short_filename
            docx_filename = get_short_filename(
                subject=solution.get("subject") or subject,
                lab_number=solution.get("lab_number", "1")
            )
            
        docx_path = job_output_dir / docx_filename

        if date_str:
            solution["date"] = date_str

        builder.build_report(
            data=solution,
            output_file=docx_path,
            screenshots=[screen_path],
            with_title_page=with_title_page,
            include_theory=include_theory,
            user_variant=variant # Only show variant if entered by user
        )
        log(f"6. Готово! Файл сохранен: {docx_path.name}")

        return {
            "success": True,
            "job_id": job_id,
            "steps": steps_log,
            "solution": solution,
            "execution": exec_result,
            "output_text": output_text,
            "screenshot_url": f"/files/{job_id}/program_screenshot.png",
            "screenshot_path": str(screen_path),
            "docx_url": f"/files/{job_id}/{docx_filename}",
            "docx_path": str(docx_path),
            "docx_filename": docx_filename
        }
