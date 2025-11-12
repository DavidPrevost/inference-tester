@echo off
REM Interactive launcher for LLM Inference Tester on Windows

:menu
cls
echo ============================================================
echo LLM Inference Tester - Main Menu
echo ============================================================
echo.
echo 1. Setup (First-time installation)
echo 2. Run Quick Test (~1 hour)
echo 3. Run Full Test (~2-4 hours)
echo 4. Run Custom Test
echo 5. Run Test Suite
echo 6. View Results (open HTML report)
echo 7. Exit
echo.
echo ============================================================

set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto setup
if "%choice%"=="2" goto quick
if "%choice%"=="3" goto full
if "%choice%"=="4" goto custom
if "%choice%"=="5" goto tests
if "%choice%"=="6" goto results
if "%choice%"=="7" goto exit
echo Invalid choice, please try again.
timeout /t 2 >nul
goto menu

:setup
echo.
echo Running setup...
call setup.bat
goto menu

:quick
echo.
echo Starting quick test mode...
echo This will test Q4_K_M and Q5_K_M quantizations (~1 hour)
echo.
call run.bat --quick
echo.
echo Test complete! Check results\report.html for detailed results.
pause
goto menu

:full
echo.
echo Starting full test mode...
echo This will test all quantization levels (~2-4 hours)
echo.
call run.bat --full
echo.
echo Test complete! Check results\report.html for detailed results.
pause
goto menu

:custom
echo.
echo Custom Test Options
echo ============================================================
echo.
echo Examples:
echo   --models "Llama-3.2-7B" --profiles interactive
echo   --quants "Q4_K_M,Q5_K_M" --skip-stress
echo   --dry-run (preview tests without running)
echo.
set /p args="Enter custom arguments: "
call run.bat %args%
echo.
pause
goto menu

:tests
echo.
echo Running test suite...
call test.bat --coverage
goto menu

:results
echo.
echo Opening results in browser...
if exist "results\report.html" (
    start results\report.html
    echo Results opened in your default browser
) else (
    echo No results found. Please run a test first.
)
pause
goto menu

:exit
echo.
echo Exiting...
exit /b 0
