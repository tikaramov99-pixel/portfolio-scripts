@echo off
rem Starts "Check the month". If Python is not on this computer yet, it is installed first,
rem once, for this user only: that is the only moment anything is downloaded.
cd /d "%~dp0"
title Check the month

rem 1. Python already here? (pyw and pythonw are the real Python, not the Store shortcut)
where pyw >nul 2>nul && (start "" pyw check_month.pyw & exit /b)
where pythonw >nul 2>nul && (start "" pythonw check_month.pyw & exit /b)
set "PYW=%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe"
if exist "%PYW%" (start "" "%PYW%" check_month.pyw & exit /b)

rem 2. Not here: install it, once
echo.
echo  Python is not on this computer yet. Installing it now from python.org (about 25 MB, once).
echo  Nothing else is installed, and nothing is sent anywhere.
echo.
winget install -e --id Python.Python.3.12 --scope user --silent --accept-package-agreements --accept-source-agreements >nul 2>nul
if not exist "%PYW%" (
  powershell -NoProfile -Command "Invoke-WebRequest 'https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe' -OutFile \"$env:TEMP\python-setup.exe\""
  "%TEMP%\python-setup.exe" /quiet InstallAllUsers=0 PrependPath=1 Include_tcltk=1 Include_launcher=1
)

rem 3. Start the program
if exist "%PYW%" (start "" "%PYW%" check_month.pyw & exit /b)
echo.
echo  Python could not be installed automatically. Please install it from https://www.python.org/downloads/
echo  (tick "Add Python to PATH"), then double-click this file again.
pause
