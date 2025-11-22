#!/usr/bin/env python3
"""
Simple script to start the backend server
"""
import subprocess
import sys
import os

def start_server():
    """Start the FastAPI server"""
    # Change to backend directory
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(backend_dir)
    
    # Activate venv and start server
    venv_python = os.path.join(backend_dir, "venv", "bin", "python")
    
    if not os.path.exists(venv_python):
        print("❌ Virtual environment not found!")
        print("Please run: python3 -m venv venv")
        sys.exit(1)
    
    print("=" * 50)
    print("Starting Backend Server")
    print("=" * 50)
    print(f"Directory: {backend_dir}")
    print(f"Python: {venv_python}")
    print("=" * 50)
    print("\nStarting uvicorn server...")
    print("Server will be available at: http://localhost:8000")
    print("Press Ctrl+C to stop the server\n")
    print("=" * 50)
    
    # Start uvicorn
    try:
        subprocess.run([
            venv_python, "-m", "uvicorn",
            "app.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
    except KeyboardInterrupt:
        print("\n\nServer stopped.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_server()

