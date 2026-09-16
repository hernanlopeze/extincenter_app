@echo off
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo Creando entorno virtual...
    python -m venv venv
    call venv\Scripts\python.exe -m pip install --upgrade pip
    call venv\Scripts\python.exe -m pip install -r requirements.txt
)

venv\Scripts\python.exe -m streamlit run app.py
pause
