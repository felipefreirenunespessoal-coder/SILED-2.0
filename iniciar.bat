@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Execute configurar_windows.bat primeiro.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" manage.py has-users
if errorlevel 1 (
    echo Execute configurar_windows.bat para configurar o primeiro acesso.
    pause
    exit /b 1
)
echo SILED em http://127.0.0.1:5000
echo Mantenha esta janela aberta enquanto utilizar o sistema.
".venv\Scripts\python.exe" main.py --open-browser
if errorlevel 1 pause
endlocal
