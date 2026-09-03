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
    custom_filename: str = Form(""),
    date_str: str = Form(""),
    include_theory: bool = Form(False),
    with_title_page: bool = Form(False),
    custom_instructions: str = Form(""),
    file: Optional[UploadFile] = File(None)
):
    try:
        uploaded_path = None
        if file and file.filename:
            upload_dir = OUTPUT_DIR / "uploads"
            upload_dir.mkdir(parents=True, exist_ok=True)
            uploaded_path = upload_dir / file.filename
            with open(uploaded_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        cfg = load_config()
        pipeline = LabPipeline(cfg)
        
        result = pipeline.run(
            task_text=task_text,
            subject=subject,
            variant=variant,
            custom_filename=custom_filename,
            date_str=date_str,
            include_theory=include_theory,
            uploaded_file=uploaded_path,
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
