@echo off
echo ==============================================
echo Python Virtual Environment Setup Script
echo ==============================================

set PYTHON_SERVERS=ai_server api_server cam_server db_server

for %%s in (%PYTHON_SERVERS%) do (
    echo.
    echo --- Setting up %%s ---
    if not exist "%%s\venv" (
        echo Creating virtual environment...
        python -m venv "%%s\venv"
    ) else (
        echo Virtual environment already exists.
    )

    if exist "%%s\requirements.txt" (
        echo Installing packages...
        call "%%s\venv\Scripts\activate.bat"
        python -m pip install --upgrade pip
        pip install -r "%%s\requirements.txt"
        call deactivate
    ) else (
        echo requirements.txt not found.
    )
)

echo.
echo --- Setting up front_server ---
if exist "front_server\package.json" (
    echo Installing npm packages...
    cd front_server
    call npm install
    cd ..
) else (
    echo package.json not found.
)

echo.
echo ==============================================
echo Setup Complete!
echo ==============================================
pause
