@echo off
REM Run script for LLM Inference Tester on Windows
REM This script activates the virtual environment and runs the tool

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Add src directory to Python path
set PYTHONPATH=%CD%\src;%PYTHONPATH%

REM Run the tool with all arguments passed through
python src\main.py %*

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

REM Deactivate virtual environment (optional)
REM call deactivate

REM Exit with the same code as the Python script
exit /b %EXIT_CODE%
