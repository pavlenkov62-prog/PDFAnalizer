@echo off
python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Код ошибки: %ERRORLEVEL%
    pause
)