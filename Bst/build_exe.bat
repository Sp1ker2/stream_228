@echo off
REM Скрипт для создания EXE файла из client_live_windows.py
REM Использует PyInstaller для компиляции

echo ========================================
echo  СОЗДАНИЕ EXE ФАЙЛА
echo ========================================
echo.

REM Проверяем наличие Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Python не найден!
    echo Установите Python 3.11+ с https://www.python.org/
    pause
    exit /b 1
)

echo [1/4] Проверка зависимостей...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo PyInstaller не найден, устанавливаю...
    pip install pyinstaller
    if errorlevel 1 (
        echo ОШИБКА: Не удалось установить PyInstaller
        pause
        exit /b 1
    )
)

echo [2/4] Установка всех зависимостей...
pip install -r requirements_windows.txt
if errorlevel 1 (
    echo ПРЕДУПРЕЖДЕНИЕ: Некоторые зависимости не установлены
)

echo [3/4] Создание EXE файла...
echo Это может занять несколько минут...
echo.

REM Создаем один EXE файл с включением всех зависимостей
pyinstaller --onefile ^
    --name "ScreenMonitorClient" ^
    --icon=NONE ^
    --hidden-import mss ^
    --hidden-import cv2 ^
    --hidden-import numpy ^
    --hidden-import requests ^
    --add-data "config.example.txt;." ^
    --console ^
    client_live_windows.py

if errorlevel 1 (
    echo.
    echo ОШИБКА: Не удалось создать EXE файл
    echo Проверьте логи выше
    pause
    exit /b 1
)

echo.
echo [4/4] Готово!
echo.
echo EXE файл создан: dist\ScreenMonitorClient.exe
echo.
echo Инструкция:
echo 1. Скопируйте ScreenMonitorClient.exe на целевую машину
echo 2. Создайте config.txt рядом с .exe
echo 3. Запустите ScreenMonitorClient.exe
echo.
pause

