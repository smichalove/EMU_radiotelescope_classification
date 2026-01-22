@echo off
:: Load the API key from config.bat
call "%~dp0config.bat"

:: Install or update required Python packages
:: python -m pip install --upgrade pip
:: pip install -r "%~dp0requirements.txt"

:: Execute the Python script
python "%~dp0emu.py"
pause