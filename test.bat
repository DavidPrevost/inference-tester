@echo off
REM Test script for LLM Inference Tester on Windows
REM This script runs the test suite using pytest

echo ============================================================
echo LLM Inference Tester - Test Suite
echo ============================================================
echo.

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

REM Parse command line arguments for test modes
set TEST_ARGS=-v

REM Check for specific test arguments
if "%1"=="--quick" (
    echo Running quick tests only...
    set TEST_ARGS=-v -m "not slow"
) else if "%1"=="--unit" (
    echo Running unit tests only...
    set TEST_ARGS=-v -m unit
) else if "%1"=="--integration" (
    echo Running integration tests only...
    set TEST_ARGS=-v -m integration
) else if "%1"=="--coverage" (
    echo Running tests with coverage report...
    set TEST_ARGS=-v --cov=src --cov-report=html --cov-report=term
) else if "%1"=="--help" (
    echo Usage: test.bat [OPTIONS]
    echo.
    echo Options:
    echo   --quick        Run only quick tests (skip slow tests)
    echo   --unit         Run only unit tests
    echo   --integration  Run only integration tests
    echo   --coverage     Run tests with coverage report
    echo   --help         Show this help message
    echo.
    echo Examples:
    echo   test.bat                Run all tests
    echo   test.bat --quick        Run quick tests
    echo   test.bat --coverage     Run with coverage report
    echo.
    goto :end
) else if not "%1"=="" (
    REM Pass through any other arguments to pytest
    set TEST_ARGS=%*
)

REM Run pytest
echo Running tests...
echo.
pytest %TEST_ARGS%

REM Capture exit code
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE% == 0 (
    echo ============================================================
    echo All tests passed!
    echo ============================================================
) else (
    echo ============================================================
    echo Some tests failed (exit code: %EXIT_CODE%)
    echo ============================================================
)
echo.

REM If coverage was run, show where the report is
if "%1"=="--coverage" (
    echo Coverage report saved to: htmlcov\index.html
    echo.
)

:end
pause
exit /b %EXIT_CODE%
