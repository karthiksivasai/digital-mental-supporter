# 🔧 RESTART SERVER - Fix Login Timeout

## The Problem
Port 8000 has processes running but they're not responding (hung/crashed). This causes login timeouts.

## ✅ SOLUTION - I've killed the hung processes

The processes on port 8000 have been killed. Now you need to **restart the server properly**.

## Steps to Fix:

### 1. Start Backend Server (IMPORTANT!)

Open a **NEW terminal** and run:

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**OR use the script I created:**

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health"
./START_SERVER.sh
```

### 2. Verify Server Started

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
INFO:     Started reloader process
```

### 3. Test Server is Working

Open browser: `http://localhost:8000/api/health`

Should see: `{"status":"healthy","version":"1.0.0"}`

### 4. Try Login Again

Once you see the server running properly, try logging in again.

## Why This Happened

The server processes were running but **hung/crashed**, so they weren't responding to requests. This causes timeouts.

## Prevention

- Always check if server is responding: `curl http://localhost:8000/api/health`
- If it hangs, kill processes: `lsof -ti:8000 | xargs kill -9`
- Then restart: `uvicorn app.main:app --reload`

## Quick Check Commands

```bash
# Check if server is running
curl http://localhost:8000/api/health

# Check what's on port 8000
lsof -i :8000

# Kill processes on port 8000
lsof -ti:8000 | xargs kill -9
```

## Next Steps

1. ✅ Processes killed (done)
2. ⏳ **YOU NEED TO:** Start the server (see Step 1 above)
3. ⏳ Verify it's working (Step 2-3)
4. ⏳ Try login again

The server should work properly now!

