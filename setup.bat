@echo off
setlocal EnableExtensions

cd /d "%~dp0"

echo.
echo ============================================================
echo   JARVIS setup
echo ============================================================
echo.
echo Read SETUP.txt if you need the full steps.
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found.
    echo Install Python 3.12+ from https://www.python.org/downloads/
    echo Enable "Add python.exe to PATH" during install.
    echo Then run setup.bat again.
    echo.
    pause
    exit /b 1
)

python --version

if not exist "venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv.
        pause
        exit /b 1
    )
)

echo.
echo Installing Python packages...
call "venv\Scripts\python.exe" -m pip install --upgrade pip
call "venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo Created .env from .env.example
    )
)

echo.
where ollama >nul 2>nul
if errorlevel 1 (
    echo [WARN] Ollama was not found.
    echo Install it from https://ollama.com/download
    echo Then run setup.bat again to download the models.
    goto done
)

echo Checking Ollama models...
ollama pull glm-4.7-flash
ollama pull qwen3.5:4b

:done
echo.
echo ============================================================
echo   Setup complete
echo ============================================================
echo.
echo Next:
echo   1. Make sure Ollama is running
echo   2. Plug in a microphone and speakers
echo   3. Run:
echo        venv\Scripts\activate
echo        python -m app.main
echo.
echo First voice run downloads the Whisper small model.
echo Full steps are in SETUP.txt
echo.
pause
endlocal
