@echo off
REM Скрипт запуска клиента на Windows

echo ========================================
echo  ЗАПУСК КЛИЕНТА МОНИТОРИНГА ЭКРАНА
echo ========================================
echo.

REM Проверяем наличие config.txt
if not exist config.txt (
    echo ОШИБКА: Файл config.txt не найден!
    echo.
    echo Создайте config.txt из config.example.txt
    echo и укажите ваш MACHINE_ID
    echo.
    pause
    exit /b 1
)

REM Проверяем, что MACHINE_ID указан
findstr /C:"MACHINE_ID=" config.txt >nul
if errorlevel 1 (
    echo ПРЕДУПРЕЖДЕНИЕ: MACHINE_ID не найден в config.txt
    echo Клиент использует имя компьютера по умолчанию
    echo.
)

echo Запуск client_live_windows.py...
echo Нажмите Ctrl+C для остановки
echo.

python client_live_windows.py

pause

