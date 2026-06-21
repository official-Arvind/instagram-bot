# Set console input/output encoding to UTF-8 to prevent emoji rendering boxes on Windows
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Console]::InputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# Execute the main bot script using the virtual environment python executable
& "$PSScriptRoot\venv\Scripts\python.exe" "$PSScriptRoot\bot.py"
