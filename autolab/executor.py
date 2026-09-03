import os
import subprocess
import tempfile
import sqlite3
import shutil
from pathlib import Path
from typing import Dict, Any, Optional

class CodeExecutor:
    @staticmethod
    def execute(
        code: str,
        language: str,
        filename: Optional[str] = None,
        test_inputs: Optional[str] = None,
        timeout: int = 15
    ) -> Dict[str, Any]:
        lang = language.lower().strip()
        result = {
            "success": False,
            "stdout": "",
            "stderr": "",
            "exit_code": -1,
            "simulated": False
        }

        if not code or not code.strip():
            result["stderr"] = "Пустой код"
            return result

        temp_dir = Path(tempfile.mkdtemp(prefix="autolab_exec_"))
        try:
            input_data = (test_inputs or "").encode("utf-8")

            if "python" in lang or lang == "py":
                file_path = temp_dir / (filename or "main.py")
                file_path.write_text(code, encoding="utf-8")
                proc = subprocess.run(
                    ["python3", str(file_path)],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                result["stdout"] = proc.stdout.decode("utf-8", errors="replace")
                result["stderr"] = proc.stderr.decode("utf-8", errors="replace")
                result["exit_code"] = proc.returncode
                result["success"] = (proc.returncode == 0)

            elif "java" in lang:
                # Find public class name if present
                class_name = "Main"
                import re
                m = re.search(r'public\s+class\s+([A-Za-z0-9_]+)', code)
                if m:
                    class_name = m.group(1)
                
                java_file = temp_dir / f"{class_name}.java"
                java_file.write_text(code, encoding="utf-8")

                compile_proc = subprocess.run(
                    ["javac", str(java_file)],
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                if compile_proc.returncode != 0:
                    result["stderr"] = "Ошибка компиляции Java:\n" + compile_proc.stderr.decode("utf-8", errors="replace")
                    result["exit_code"] = compile_proc.returncode
                    return result

                run_proc = subprocess.run(
                    ["java", class_name],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                result["stdout"] = run_proc.stdout.decode("utf-8", errors="replace")
                result["stderr"] = run_proc.stderr.decode("utf-8", errors="replace")
                result["exit_code"] = run_proc.returncode
                result["success"] = (run_proc.returncode == 0)

            elif "cpp" in lang or "c++" in lang:
                src_file = temp_dir / (filename or "solution.cpp")
                src_file.write_text(code, encoding="utf-8")
                bin_file = temp_dir / "solution"

                compile_proc = subprocess.run(
                    ["g++", "-O2", str(src_file), "-o", str(bin_file), "-lm"],
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                if compile_proc.returncode != 0:
                    result["stderr"] = "Ошибка компиляции C++:\n" + compile_proc.stderr.decode("utf-8", errors="replace")
                    result["exit_code"] = compile_proc.returncode
                    return result

                run_proc = subprocess.run(
                    [str(bin_file)],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                result["stdout"] = run_proc.stdout.decode("utf-8", errors="replace")
                result["stderr"] = run_proc.stderr.decode("utf-8", errors="replace")
                result["exit_code"] = run_proc.returncode
                result["success"] = (run_proc.returncode == 0)

            elif lang == "c":
                src_file = temp_dir / (filename or "solution.c")
                src_file.write_text(code, encoding="utf-8")
                bin_file = temp_dir / "solution"

                compile_proc = subprocess.run(
                    ["gcc", "-O2", str(src_file), "-o", str(bin_file), "-lm"],
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                if compile_proc.returncode != 0:
                    result["stderr"] = "Ошибка компиляции C:\n" + compile_proc.stderr.decode("utf-8", errors="replace")
                    result["exit_code"] = compile_proc.returncode
                    return result

                run_proc = subprocess.run(
                    [str(bin_file)],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                result["stdout"] = run_proc.stdout.decode("utf-8", errors="replace")
                result["stderr"] = run_proc.stderr.decode("utf-8", errors="replace")
                result["exit_code"] = run_proc.returncode
                result["success"] = (run_proc.returncode == 0)

            elif "sql" in lang:
                # Execute in SQLite
                db_path = temp_dir / "database.db"
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                output_lines = []
                try:
                    # Execute script
                    cursor.executescript(code)
                    conn.commit()
                    output_lines.append("✓ Скрипт SQL успешно выполнен без ошибок.")
                    
                    # Inspect tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                    tables = cursor.fetchall()
                    for (tbl,) in tables:
                        output_lines.append(f"\n[Таблица: {tbl}]")
                        cursor.execute(f"PRAGMA table_info({tbl});")
                        cols = [c[1] for c in cursor.fetchall()]
                        output_lines.append(" | ".join(cols))
                        output_lines.append("-" * 40)
                        cursor.execute(f"SELECT * FROM {tbl} LIMIT 10;")
                        for row in cursor.fetchall():
                            output_lines.append(" | ".join([str(v) for v in row]))
                    result["stdout"] = "\n".join(output_lines)
                    result["success"] = True
                    result["exit_code"] = 0
                except Exception as sqle:
                    result["stderr"] = f"SQL Error: {sqle}"
                finally:
                    conn.close()

            elif "bash" in lang or "sh" in lang:
                src_file = temp_dir / "script.sh"
                src_file.write_text(code, encoding="utf-8")
                run_proc = subprocess.run(
                    ["bash", str(src_file)],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                result["stdout"] = run_proc.stdout.decode("utf-8", errors="replace")
                result["stderr"] = run_proc.stderr.decode("utf-8", errors="replace")
                result["exit_code"] = run_proc.returncode
                result["success"] = (run_proc.returncode == 0)

            elif "js" in lang or "node" in lang:
                src_file = temp_dir / "solution.js"
                src_file.write_text(code, encoding="utf-8")
                run_proc = subprocess.run(
                    ["node", str(src_file)],
                    input=input_data,
                    capture_output=True,
                    timeout=timeout,
                    cwd=str(temp_dir)
                )
                result["stdout"] = run_proc.stdout.decode("utf-8", errors="replace")
                result["stderr"] = run_proc.stderr.decode("utf-8", errors="replace")
                result["exit_code"] = run_proc.returncode
                result["success"] = (run_proc.returncode == 0)

            else:
                # General fallback: python syntax check or simulated
                result["simulated"] = True
                result["stdout"] = "Выполнение эмулировано для среды: " + lang
                result["success"] = True
                result["exit_code"] = 0

        except subprocess.TimeoutExpired:
            result["stderr"] = f"Превышено время ожидания ({timeout} с)."
        except Exception as e:
            result["stderr"] = f"Системная ошибка запуска: {e}"
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        return result
