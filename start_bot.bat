@echo off

:: Check if %0 is %~nx0
if not %0 == %~nx0 (
    echo Starting myself in window that stays open...
    timeout 1
    start cmd /k %~nx0
    exit
)

:: Start the environment
echo Starting the environment...
call .venv\Scripts\activate.bat

cd src
py main.py