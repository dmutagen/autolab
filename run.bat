@echo off
chcp 65001 > nul
echo =========================================================
echo   AutoLab AI - Генератор лабораторных по ГОСТу РБ
echo =========================================================

if not exist ".venv\Scripts\python.exe" (
    echo Создание виртуального окружения...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)

if "%~1"=="" (
    echo Веб-интерфейс запускается на http://127.0.0.1:8000
    python -m uvicorn server:app --host 127.0.0.1 --port 8000
) else (
    python cli.py %*
)
pause
