@echo off
setlocal
cd /d "%~dp0"
where code >nul 2>nul
if not errorlevel 1 (
    code "%~dp0SILED.code-workspace"
    exit /b 0
)
if exist "%LocalAppData%\Programs\Microsoft VS Code\Code.exe" (
    start "" "%LocalAppData%\Programs\Microsoft VS Code\Code.exe" "%~dp0SILED.code-workspace"
    exit /b 0
)
if exist "%ProgramFiles%\Microsoft VS Code\Code.exe" (
    start "" "%ProgramFiles%\Microsoft VS Code\Code.exe" "%~dp0SILED.code-workspace"
    exit /b 0
)
echo VS Code nao encontrado. Abra SILED.code-workspace pelo VS Code.
pause
exit /b 1
