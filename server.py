import os
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from autolab.config import AppConfig, load_config, save_config, OUTPUT_DIR, CONFIG_FILE
from autolab.pipeline import LabPipeline

app = FastAPI(title="AutoLab AI", description="Автогенератор лабораторных работ по Белорусскому ГОСТу")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
async def root():
    return FileResponse(str(static_dir / "index.html"))

@app.get("/api/config")
async def get_config():
    cfg = load_config()
    data = cfg.model_dump()
    key = cfg.gemini_api_key
    if key and len(key) > 8:
        data["masked_api_key"] = f"{key[:4]}...{key[-4:]}"
    else:
        data["masked_api_key"] = ""
    return data

class ConfigUpdate(BaseModel):
    gemini_api_key: Optional[str] = None
    model_name: Optional[str] = None
    student_name: Optional[str] = None
    group: Optional[str] = None
    teacher_name: Optional[str] = None
    institution: Optional[str] = None
    specialty: Optional[str] = None

@app.post("/api/config")
async def update_config(update: ConfigUpdate):
    cfg = load_config()
    if update.gemini_api_key is not None and update.gemini_api_key.strip():
        cfg.gemini_api_key = update.gemini_api_key.strip()
    if update.model_name is not None and update.model_name.strip():
        cfg.model_name = update.model_name.strip()
    if update.student_name is not None:
        cfg.student.student_name = update.student_name.strip()
    if update.group is not None:
        cfg.student.group = update.group.strip()
    if update.teacher_name is not None:
        cfg.student.teacher_name = update.teacher_name.strip()
    if update.institution is not None:
        cfg.student.institution = update.institution.strip()
    if update.specialty is not None:
        cfg.student.specialty = update.specialty.strip()
    
    save_config(cfg)
    return {"success": True, "message": "Настройки успешно сохранены!"}

@app.post("/api/generate")
async def generate_lab(
    task_text: str = Form(""),
    subject: str = Form(""),
    variant: str = Form(""),
    custom_code: str = Form(""),
    custom_filename: str = Form(""),
    date_str: str = Form(""),
    include_theory: bool = Form(False),
    with_title_page: bool = Form(False),
    custom_instructions: str = Form(""),
    file: Optional[UploadFile] = File(None),
    files: List[UploadFile] = File(None),
    code_file: Optional[UploadFile] = File(None),
    screenshots: List[UploadFile] = File(None)
):
    try:
        upload_dir = OUTPUT_DIR / "uploads"
        upload_dir.mkdir(parents=True, exist_ok=True)

        # 1. Main task and reference files (PDF, DOCX, IMAGES, LECTURES)
        uploaded_task_files = []
        if files:
            for f_item in files:
                if f_item and f_item.filename:
                    t_path = upload_dir / f_item.filename
                    with open(t_path, "wb") as buffer:
                        shutil.copyfileobj(f_item.file, buffer)
                    uploaded_task_files.append(t_path)
        if file and file.filename:
            t_path = upload_dir / file.filename
            with open(t_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            if t_path not in uploaded_task_files:
                uploaded_task_files.append(t_path)

        # 2. Custom code from file or textarea
        resolved_code = custom_code.strip() if custom_code else ""
        if code_file and code_file.filename:
            c_path = upload_dir / code_file.filename
            with open(c_path, "wb") as buffer:
                shutil.copyfileobj(code_file.file, buffer)
            try:
                with open(c_path, "r", encoding="utf-8", errors="replace") as f:
                    file_code = f.read().strip()
                    if file_code:
                        resolved_code = file_code
            except Exception as e:
                print(f"Warning: Failed to read code file {c_path}: {e}")

        # 3. User screenshots
        user_screenshot_paths = []
        if screenshots:
            for s_file in screenshots:
                if s_file and s_file.filename:
                    s_path = upload_dir / f"user_shot_{s_file.filename}"
                    with open(s_path, "wb") as buffer:
                        shutil.copyfileobj(s_file.file, buffer)
                    user_screenshot_paths.append(s_path)

        cfg = load_config()
        pipeline = LabPipeline(cfg)
        
        result = pipeline.run(
            task_text=task_text,
            subject=subject,
            variant=variant,
            custom_code=resolved_code,
            custom_filename=custom_filename,
            date_str=date_str,
            include_theory=include_theory,
            uploaded_files=uploaded_task_files if uploaded_task_files else None,
            user_screenshots=user_screenshot_paths if user_screenshot_paths else None,
            with_title_page=with_title_page,
            custom_instructions=custom_instructions
        )
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/files/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = OUTPUT_DIR / f"lab_{job_id}" / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    return FileResponse(str(file_path), filename=filename)

@app.get("/api/history")
async def get_history():
    history = []
    if OUTPUT_DIR.exists():
        for job_folder in sorted(OUTPUT_DIR.glob("lab_*"), key=lambda p: p.stat().st_mtime, reverse=True):
            docx_files = list(job_folder.glob("*.docx"))
            if docx_files:
                doc = docx_files[0]
                history.append({
                    "job_id": job_folder.name.replace("lab_", ""),
                    "docx_filename": doc.name,
                    "docx_url": f"/files/{job_folder.name.replace('lab_', '')}/{doc.name}",
                    "created_at": doc.stat().st_mtime
                })
    return history[:10]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)
