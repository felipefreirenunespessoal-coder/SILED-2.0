$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path '.venv\Scripts\python.exe')) {
    py -3 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Nao foi possivel criar a .venv.' }
}
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Falha ao instalar dependencias.' }
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
& '.\.venv\Scripts\python.exe' manage.py has-users
if ($LASTEXITCODE -eq 1) {
    & '.\.venv\Scripts\python.exe' manage.py create-user --role administrador
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao cadastrar administrador.' }
} elseif ($LASTEXITCODE -ne 0) { throw 'Falha ao verificar banco de dados.' }
Write-Host 'Configuracao concluida. Execute iniciar.bat.'
