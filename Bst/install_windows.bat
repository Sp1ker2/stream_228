@echo off
REM Скрипт установки для Windows
REM Установит Python зависимости и настроит клиент

echo ========================================
echo  УСТАНОВКА КЛИЕНТА МОНИТОРИНГА ЭКРАНА
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

echo [1/3] Python найден
python --version

REM Проверяем наличие pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: pip не найден!
    pause
    exit /b 1
)

echo [2/3] Установка зависимостей...
pip install -r requirements_windows.txt

if errorlevel 1 (
    echo ОШИБКА: Не удалось установить зависимости
    pause
    exit /b 1
)

echo [3/3] Настройка конфигурации...
if not exist config.txt (
    echo Создаю config.txt из шаблона...
    copy config.example.txt config.txt
    echo.
    echo ВАЖНО: Отредактируйте config.txt и укажите ваш MACHINE_ID!
    echo Например: MACHINE_ID=Иван_Desktop
    echo.
    pause
)

echo.
echo ========================================
echo  УСТАНОВКА ЗАВЕРШЕНА
echo ========================================
echo.
echo Для запуска используйте:
echo   python client_live_windows.py
echo.
echo Или запустите start_client.bat
echo.
pause

