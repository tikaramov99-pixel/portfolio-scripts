@echo off
cd /d "%~dp0"
echo.
echo  Confidential data, analysed offline
echo  The first start installs 3 Python packages (needs internet, once). After that it works offline.
echo.
python -m pip install --quiet -r requirements.txt
python -m streamlit run app.py
pause
