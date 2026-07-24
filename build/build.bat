@echo off
REM ============================================================
REM HiveOS One-Click Build Script
REM Produces a single .exe installer for Windows
REM
REM Usage: Double-click build.bat  or  build.bat
REM Prerequisites: Python 3.11+ in PATH or project .venv
REM ============================================================

setlocal
cd /d "%~dp0.."

echo.
echo  ========================================
echo   HiveOS Windows Build
echo  ========================================
echo.

REM Check for project venv
if exist ".venv\Scripts\python.exe" (
    set PYTHON=.venv\Scripts\python.exe
    echo  [OK] Using project venv Python
) else (
    set PYTHON=python
    echo  [OK] Using system Python
)

REM Check Python version
%PYTHON% --version 2>nul
if errorlevel 1 (
    echo  [ERROR] Python not found. Install Python 3.11+
    pause
    exit /b 1
)

REM Install build dependencies
echo.
echo  Installing build dependencies...
%PYTHON% -m pip install --quiet pyinstaller 2>nul

REM Run the build
echo.
echo  Building HiveOS.exe...
%PYTHON% build\build_exe.py %*

if errorlevel 1 (
    echo.
    echo  [ERROR] Build failed. Check output above.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Build complete!
echo  ========================================
echo.
echo  Output: dist\HiveOS.exe
echo.
echo  To create an installer (.exe setup):
echo    1. Install Inno Setup: https://jrsoftware.org/isdl.php
echo    2. Run: build\build_installer.bat
echo.
echo  Or distribute dist\HiveOS.exe directly.
echo.

pause
