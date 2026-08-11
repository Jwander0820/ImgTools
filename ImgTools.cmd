@echo off
setlocal

cd /d "%~dp0"
title ImgTools UI - Close this window to stop

set "PYTHON_EXE=%LOCALAPPDATA%\Python\bin\python.exe"

if not exist "%PYTHON_EXE%" (
    echo Python was not found at:
    echo   "%PYTHON_EXE%"
    echo.
    echo ImgTools could not start.
    pause
    exit /b 1
)

echo ImgTools is starting...
echo Close this CMD window to stop ImgTools.
echo.

"%PYTHON_EXE%" "%~dp0main.py"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo ImgTools stopped with exit code %EXIT_CODE%.
    pause
)

exit /b %EXIT_CODE%
