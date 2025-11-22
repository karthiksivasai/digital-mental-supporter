# 🚀 START BACKEND SERVER - FIX ERR_CONNECTION_REFUSED

## The Problem
`ERR_CONNECTION_REFUSED` means **the backend server is NOT running**.

## ✅ SOLUTION: Start the Backend Server

### Step 1: Open a Terminal

Open a **NEW terminal window** (keep it open - you'll see server logs here)

### Step 2: Navigate to Backend Folder

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
```

### Step 3: Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your prompt.

### Step 4: Start the Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: Verify It's Running

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 6: Test in Browser

Open: `http://localhost:8000/api/health`

Should see: `{"status":"healthy","version":"1.0.0"}`

### Step 7: Try Login Again

Once you see the server running and `/api/health` works, try logging in again!

## ⚠️ Important Notes

- **Keep the terminal open** - Closing it stops the server
- **Don't close the terminal** - The server needs to keep running
- **Press Ctrl+C** to stop the server when done

## 🔄 Quick Start Script

I've created a script to make this easier:

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health"
./START_SERVER.sh
```

This will:
- Check virtual environment
- Install dependencies if needed
- Kill any existing processes on port 8000
- Start the server

## ✅ Checklist

- [ ] Terminal opened
- [ ] Navigated to backend folder
- [ ] Virtual environment activated (see `venv` in prompt)
- [ ] Server started (see "Uvicorn running" message)
- [ ] `/api/health` works in browser
- [ ] Try login again

## 🐛 If Server Won't Start

**Error: "Module not found"**
```bash
pip install -r requirements.txt
```

**Error: "Port already in use"**
```bash
lsof -ti:8000 | xargs kill -9
```

**Error: "No module named 'app'"**
- Make sure you're in the `backend` folder
- Check: `ls app/main.py` should work

## 📝 What You Should See

When server is running correctly:
```
(venv) user@computer backend % uvicorn app.main:app --reload
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Once you see this, the server is running and login should work!**

