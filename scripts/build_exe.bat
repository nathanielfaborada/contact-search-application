:: Utility Script: Single-click PyInstaller compiler
@echo off
echo ==============================================
echo Building Phonebook Desktop Standalone (.EXE)...
echo ==============================================

python -m pip install pyinstaller --quiet
pyinstaller --noconsole --onefile --name "Phonebook" --add-data "contacts.json;." main.py

echo.
echo ==============================================
echo Build completed successfully!
echo Output file: dist\Phonebook.exe
echo ==============================================
pause
