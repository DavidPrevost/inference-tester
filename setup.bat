@echo off
REM Setup script for LLM Inference Tester on Windows
REM This script sets up the Python environment and installs dependencies

echo ============================================================
echo LLM Inference Tester - Setup
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or later from https://www.python.org
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

REM Check Python version (must be 3.8 or later)
python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python 3.8 or later is required
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
    echo.
) else (
    echo Virtual environment already exists
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo.

REM Install dependencies
echo Installing dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo WARNING: requirements.txt not found
    echo Installing core dependencies...
    pip install pyyaml requests pytest pytest-cov
)
echo.

REM Create necessary directories
echo Creating directories...
if not exist "models" mkdir models
if not exist "results" mkdir results
if not exist "data" mkdir data
echo.

REM Check for config files
echo Checking configuration files...
if not exist "config.yaml" (
    if exist "config.example.yaml" (
        echo Creating config.yaml from example...
        copy config.example.yaml config.yaml
    ) else (
        echo WARNING: config.example.yaml not found
        echo You'll need to create config.yaml manually
    )
)

if not exist "models.yaml" (
    if exist "models.example.yaml" (
        echo Creating models.yaml from example...
        copy models.example.yaml models.yaml
    ) else (
        echo WARNING: models.example.yaml not found
        echo You'll need to create models.yaml manually
    )
)
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next steps:
echo   1. Edit config.yaml to configure your llama.cpp server path
echo   2. Edit models.yaml to select which models to test
echo   3. Download llama.cpp server from https://github.com/ggerganov/llama.cpp
echo   4. Place your GGUF model files in the models/ directory
echo   5. Run: run.bat --quick    (for a quick test)
echo      or:  run.bat --full     (for comprehensive testing)
echo.
echo To activate the virtual environment manually:
echo   venv\Scripts\activate.bat
echo.

pause
