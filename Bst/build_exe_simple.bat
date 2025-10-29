@echo off
REM Упрощенная версия - создает один EXE без консоли (для фонового запуска)

echo ========================================
echo  СОЗДАНИЕ EXE (БЕЗ КОНСОЛИ)
echo ========================================
echo.

python --version >nul 2>&1 || (
    echo ОШИБКА: Python не найден!
    pause
    exit /b 1
)

pip install pyinstaller >nul 2>&1
pip install -r requirements_windows.txt

echo Создание EXE (без окна консоли)...
pyinstaller --onefile --noconsole ^
    --name "ScreenMonitorClient" ^
    --hidden-import mss ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import requests ^
    --add-data "config.example.txt;." ^
    client_live_windows.py

if errorlevel 0 (
    echo.
    echo ✅ Готово! EXE: dist\ScreenMonitorClient.exe
    echo При запуске не будет окна консоли.
) else (
    echo.
    echo ❌ Ошибка создания EXE
)

pause

