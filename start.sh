#!/bin/bash
echo "============================================================"
echo "  ASTERIC RISKIQ - Hospital Readmission Prediction AI"
echo "  Starting System..."
echo "============================================================"

# Start Backend
echo "[1/2] Starting Backend (Python FastAPI)..."
cd backend
pip install -r requirements.txt > /dev/null 2>&1
python run.py &
BACKEND_PID=$!
cd ..

# Wait for backend
echo "Waiting for backend to initialize..."
sleep 15

# Start Frontend
echo "[2/2] Starting Frontend (Next.js)..."
cd frontend
npm install > /dev/null 2>&1
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "============================================================"
echo "  Asteric RiskIQ is running!"
echo ""
echo "  Backend API:    http://localhost:8000"
echo "  API Docs:       http://localhost:8000/docs"
echo "  Frontend:       http://localhost:3000"
echo ""
echo "  Press Ctrl+C to stop all services"
echo "============================================================"

# Trap to cleanup
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null" EXIT

wait
