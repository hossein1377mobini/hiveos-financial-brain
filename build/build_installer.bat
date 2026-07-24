@echo off
REM ============================================================
REM HiveOS Inno Setup Installer Builder
REM Produces a .exe setup installer (HiveOS-Setup-x.x.x.exe)
REM
REM Prerequisites:
REM   1. Run build.bat first (produces dist\HiveOS.exe or dist\HiveOS\)
REM   2. Install Inno Setup 6: https://jrsoftware.org/isdl.php
REM ============================================================

setlocal
cd /d "%~dp0"

echo.
echo  ========================================
echo   HiveOS Installer Build
echo  ========================================
echo.

REM Check if dist/HiveOS.exe or dist/HiveOS/ exists
if not exist "..\dist\HiveOS.exe" (
    if not exist "..\dist\HiveOS\HiveOS.exe" (
        echo  [ERROR] dist\HiveOS.exe not found.
        echo  Run build.bat first.
        pause
        exit /b 1
    )
)

REM Find Inno Setup
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\iscc.exe" (
    set ISCC=C:\Program Files (x86)\Inno Setup 6\iscc.exe
) else if exist "C:\Program Files\Inno Setup 6\iscc.exe" (
    set ISCC=C:\Program Files\Inno Setup 6\iscc.exe
) else (
    where iscc >nul 2>&1 && set ISCC=iscc
)

if "%ISCC%"=="" (
    echo  [ERROR] Inno Setup not found.
    echo  Download: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

echo  Using: %ISCC%
echo  Compiling installer...
echo.

"%ISCC%" installer.iss

if errorlevel 1 (
    echo.
    echo  [ERROR] Inno Setup compilation failed.
    pause
    exit /b 1
)

echo.
echo  ========================================
echo   Installer built successfully!
echo  ========================================
echo.
echo  Output: ..\dist\HiveOS-Setup-*.exe
echo.

pause
