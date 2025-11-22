#!/bin/bash
# Double-click this file to start the server

cd "$(dirname "$0")"
echo "=========================================="
echo "Starting Backend Server"
echo "=========================================="
echo ""
echo "This window must stay open!"
echo "Server will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="
echo ""

source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

