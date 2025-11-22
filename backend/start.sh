#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
echo "Starting server on http://localhost:8000"
echo "Press Ctrl+C to stop"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
