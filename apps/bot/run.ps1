# Run shop bot (polling). Requires .env in repo root with BOT_TOKEN.
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path .venv\Scripts\python.exe)) {
  python -m venv .venv
  .\.venv\Scripts\python.exe -m pip install -U pip
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  .\.venv\Scripts\python.exe -m pip install -e ..\..\packages\mtproto
}
.\.venv\Scripts\python.exe -m bot_app.main
