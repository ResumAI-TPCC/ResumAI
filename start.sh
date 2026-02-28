#!/bin/bash

# ResumAI Local Development Startup Script
# Usage: ./start.sh

PROJECT_ROOT="/Users/fengbowen/Desktop/resumai"

echo "🚀 Starting ResumAI..."

# Kill existing processes on ports 8000 and 5173
echo "Cleaning up existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:5173 | xargs kill -9 2>/dev/null

# Start Backend
echo "Starting Backend on http://localhost:8000..."
cd "$PROJECT_ROOT/backend"
source venv/bin/activate 2>/dev/null || true
python run.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Start Frontend
echo "Starting Frontend on http://localhost:5173..."
cd "$PROJECT_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ ResumAI is running!"
echo "   Backend:  http://localhost:8000"
echo "   Frontend: http://localhost:5173"
echo ""
echo "Press Ctrl+C to stop all services"

# Wait for Ctrl+C
trap "echo 'Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

wait
