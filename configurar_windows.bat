@echo off
setlocal
cd /d "%~dp0"
echo ============================================
echo SILED - Configuracao inicial
echo ============================================
if not exist ".venv\Scripts\python.exe" (
    where py >nul 2>nul
    if errorlevel 1 (
        echo [ERRO] Instale Python 3.10 ou superior com o Python Launcher.
        pause
        exit /b 1
    )
    py -3 -m venv .venv
    if errorlevel 1 goto erro
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto erro
if not exist .env copy /y .env.example .env >nul
".venv\Scripts\python.exe" manage.py has-users
if errorlevel 2 goto erro
if errorlevel 1 (
    echo Cadastre agora o primeiro administrador.
    ".venv\Scripts\python.exe" manage.py create-user --role administrador
    if errorlevel 1 goto erro
)
echo [OK] Configuracao concluida. Execute iniciar.bat.
pause
exit /b 0
:erro
echo [ERRO] A configuracao nao foi concluida. Confira a mensagem acima.
pause
exit /b 1
