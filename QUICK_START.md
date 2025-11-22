# 🚀 QUICK START - Fix ERR_CONNECTION_REFUSED

## The Error
`ERR_CONNECTION_REFUSED` means the backend server is **NOT running**.

## ✅ SOLUTION: Start the Server

### Method 1: Using Python Script (Easiest)

Open a **NEW terminal** and run:

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
python3 start_server.py
```

### Method 2: Manual Start

Open a **NEW terminal** and run:

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Method 3: Using Start Script

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health"
./START_SERVER.sh
```

## ✅ What You Should See

When server starts successfully:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

## ✅ Verify It's Working

1. Open browser: `http://localhost:8000/api/health`
2. Should see: `{"status":"healthy","version":"1.0.0"}`
3. If you see this, server is running! ✅

## ✅ Then Try Login

Once server is running, go back to your login page and try again!

## ⚠️ IMPORTANT

- **Keep the terminal open** - Don't close it!
- The server must keep running while you use the app
- Press `Ctrl+C` to stop when done

## 🐛 Troubleshooting

**If you get "Module not found":**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

**If port is already in use:**
```bash
lsof -ti:8000 | xargs kill -9
```

**If virtual environment doesn't exist:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 📝 Summary

1. ✅ Open terminal
2. ✅ Run: `cd backend && python3 start_server.py`
3. ✅ Wait for "Uvicorn running" message
4. ✅ Test: `http://localhost:8000/api/health`
5. ✅ Try login again!

The server is the missing piece - once it's running, everything will work!

