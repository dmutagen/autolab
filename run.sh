#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

VENV_PY="$DIR/.venv/bin/python"

if [ ! -f "$VENV_PY" ]; then
    echo "Создание виртуального окружения..."
    if command -v uv &> /dev/null; then
        uv venv "$DIR/.venv"
        VIRTUAL_ENV="$DIR/.venv" uv pip install -r "$DIR/requirements.txt"
    else
        python3 -m venv "$DIR/.venv"
        "$DIR/.venv/bin/pip" install -r "$DIR/requirements.txt"
    fi
fi

if [ "$#" -gt 0 ]; then
    # Pass arguments to CLI
    "$VENV_PY" "$DIR/cli.py" "$@"
else
    # Launch Web Server
    echo "========================================================="
    echo "  🚀 AutoLab AI — Генератор лабораторных по ГОСТу РБ"
    echo "========================================================="
    echo "Веб-интерфейс доступен по адресу:"
    echo "👉 http://127.0.0.1:8000"
    echo "Нажмите Ctrl+C для остановки."
    echo "========================================================="
    "$VENV_PY" -m uvicorn server:app --host 127.0.0.1 --port 8000
fi
