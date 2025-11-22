#!/bin/bash
# Script to start the backend server

cd "$(dirname "$0")/backend"

echo "=========================================="
echo "Starting Backend Server"
echo "=========================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if port is already in use
if lsof -ti:8000 > /dev/null 2>&1; then
    echo "⚠️  Port 8000 is already in use!"
    echo "Killing existing process..."
    lsof -ti:8000 | xargs kill -9
    sleep 2
fi

# Start the server
echo ""
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
echo "=========================================="
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

