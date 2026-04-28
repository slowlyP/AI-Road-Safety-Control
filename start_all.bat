@echo off
echo ==============================================
echo Starting All Microservices
echo ==============================================
echo Each server will open in a new window.

echo Starting DB Server...
start "DB Server (Port 5000)" cmd /k "cd db_server && call venv\Scripts\activate.bat && python run.py"

echo Starting API Server...
start "API Server (Port 5001)" cmd /k "cd api_server && call venv\Scripts\activate.bat && python run.py"

echo Starting AI Server...
start "AI Server (Port 5002)" cmd /k "cd ai_server && call venv\Scripts\activate.bat && python run.py"

echo Starting Cam Server...
start "Cam Server (Port 5003)" cmd /k "cd cam_server && call venv\Scripts\activate.bat && python run.py"

echo Starting Front Server...
start "Front Server (Port 5173)" cmd /k "cd front_server && npm run dev"

echo.
echo All servers are starting. You can close this window.
pause
