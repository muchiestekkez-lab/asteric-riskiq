@echo off
echo ============================================================
echo   ASTERIC RISKIQ - Hospital Readmission Prediction AI
echo   Starting System...
echo ============================================================
echo.

:: Start Backend
echo [1/2] Starting Backend (Python FastAPI)...
cd backend
start "Asteric RiskIQ Backend" cmd /k "pip install -r requirements.txt && python run.py"
cd ..

:: Wait for backend to initialize
echo Waiting for backend to initialize...
timeout /t 15 /nobreak > nul

:: Start Frontend
echo [2/2] Starting Frontend (Next.js)...
cd frontend
start "Asteric RiskIQ Frontend" cmd /k "npm install && npm run dev"
cd ..

echo.
echo ============================================================
echo   Asteric RiskIQ is starting up!
echo.
echo   Backend API:    http://localhost:8000
echo   API Docs:       http://localhost:8000/docs
echo   Frontend:       http://localhost:3000
echo.
echo   First startup takes ~60 seconds (model training)
echo ============================================================
