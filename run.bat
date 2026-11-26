@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" goto dependencies
where py.exe >nul 2>nul
if errorlevel 1 goto use_python
py -3 -m venv .venv
if not errorlevel 1 goto dependencies
:use_python
python -m venv .venv
if errorlevel 1 goto no_python
:dependencies
".venv\Scripts\python.exe" -c "import streamlit, PIL; assert streamlit.__version__ == '1.51.0'" >nul 2>nul
if not errorlevel 1 goto launch
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed
:launch
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto failed
exit /b 0
:no_python
echo Install Python 3.12 and enable its launcher or Add Python to PATH, then try again.
:failed
pause
exit /b 1
