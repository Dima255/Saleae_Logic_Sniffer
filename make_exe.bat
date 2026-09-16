@echo off
chcp 65001 >nul
title Сборка Saleae Parser

echo ============================================================
echo   СБОРКА SALE AE PARSER - PYINSTALLER
echo ============================================================
echo.

:: Проверка наличия Python
echo [1/6] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не найден! Установите Python и добавьте в PATH.
    pause
    exit /b 1
)
python --version
echo.

:: Проверка наличия pip
echo [2/6] Проверка pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] pip не найден!
    pause
    exit /b 1
)
pip --version
echo.

:: Проверка наличия виртуального окружения
echo [3/6] Проверка виртуального окружения...
if not exist "venv" (
    echo Создание виртуального окружения...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение!
        pause
        exit /b 1
    )
    echo [+] Виртуальное окружение создано
) else (
    echo [+] Виртуальное окружение уже существует
)
echo.

:: Активация виртуального окружения
echo [4/6] Активация виртуального окружения...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось активировать виртуальное окружение!
    pause
    exit /b 1
)
echo [+] Виртуальное окружение активировано
echo.

:: Установка PyInstaller
echo [5/6] Установка PyInstaller...
pip install --upgrade pip >nul 2>&1
pip install pyinstaller
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить PyInstaller!
    pause
    exit /b 1
)
echo [+] PyInstaller установлен
echo.

:: Проверка наличия исходного файла
echo [6/6] Проверка исходного файла...
if not exist "Saleae_Logic_Sniffer.py" (
    echo [ОШИБКА] Файл Saleae_Logic_Sniffer.py не найден!
    echo.
    echo Список .py файлов в папке:
    dir *.py 2>nul
    echo.
    pause
    exit /b 1
)
echo [+] Исходный файл найден: Saleae_Logic_Sniffer.py
echo.

:: Сборка .exe
echo ============================================================
echo   НАЧАЛО СБОРКИ...
echo ============================================================
echo.

pyinstaller --onefile --windowed --name="Saleae_Parser" Saleae_Logic_Sniffer.py

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Сборка завершилась с ошибкой!
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   СБОРКА УСПЕШНО ЗАВЕРШЕНА!
echo ============================================================
echo.
echo [+] Готовый файл: dist\Saleae_Parser.exe
echo.
echo Размер файла:
dir dist\Saleae_Parser.exe 2>nul
echo.
echo ============================================================
echo.

:: Деактивация виртуального окружения
call venv\Scripts\deactivate.bat

:: Вопрос об открытии папки
choice /C YN /M "Открыть папку dist?"
if %errorlevel%==1 (
    start "" dist
)

pause