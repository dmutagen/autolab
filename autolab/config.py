import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "output"
CONFIG_FILE = BASE_DIR / "config.json"
KB_FILE = BASE_DIR / "autolab" / "knowledge_base.json"

MODELS_CASCADE = [
    "gemini-2.5-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-2.5-flash-lite",
    "gemini-3.1-flash-lite"
]

class StudentProfile(BaseModel):
    institution: str = "Учреждение образования «Гомельский государственный машиностроительный колледж»"
    specialty: str = "5-04-0611-01 «Программирование мобильных устройств»"
    group: str = "ПМ-31"
    student_name: str = "Кашевич Е.Н."
    teacher_name: str = "Фамилия И.О."
    city: str = "Гомель"
    year: str = "2026"

class GostSettings(BaseModel):
    font_name: str = "Times New Roman"
    font_size_pt: int = 14
    line_spacing: float = 1.0
    first_line_indent_cm: float = 1.25
    margin_left_mm: int = 30
    margin_right_mm: int = 10
    margin_top_mm: int = 20
    margin_bottom_mm: int = 20
    code_font_name: str = "Times New Roman"
    code_font_size_pt: int = 11

class AppConfig(BaseModel):
    gemini_api_key: str = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model_name: str = "gemini-2.5-flash"
    student: StudentProfile = Field(default_factory=StudentProfile)
    gost: GostSettings = Field(default_factory=GostSettings)

def load_config() -> AppConfig:
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return AppConfig(**data)
        except Exception as e:
            print(f"Warning: Failed to load config from {CONFIG_FILE}: {e}")
    
    cfg = AppConfig()
    save_config(cfg)
    return cfg

def save_config(config: AppConfig) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2))
