# Quick Fix for Login Timeout

## The Problem
Login request is timing out after 30 seconds. This usually means:
1. **Backend server is NOT running** (most common)
2. Backend server is running but not responding
3. Connection issue between frontend and backend

## Quick Fix Steps

### Step 1: Check if Backend Server is Running

Open a terminal and check:
```bash
# Check if port 8000 is in use
lsof -i :8000
# OR on Windows:
netstat -ano | findstr :8000
```

If nothing shows up, **the server is NOT running**.

### Step 2: Start the Backend Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### Step 3: Verify Server is Working

Open your browser and go to:
```
http://localhost:8000/api/health
```

You should see:
```json
{"status":"healthy","version":"1.0.0"}
```

If you see this, the server is working!

### Step 4: Check Frontend Connection

Make sure your frontend is connecting to the right URL:
- Check `.env` file in frontend folder for `NEXT_PUBLIC_API_URL`
- Should be: `http://localhost:8000` or `http://127.0.0.1:8000`

### Step 5: Try Login Again

Once the server is running and you can access `/api/health`, try logging in again.

## Common Issues

### Issue: "Connection refused"
**Solution:** Backend server is not running. Start it using Step 2.

### Issue: Server starts but crashes immediately
**Solution:** Check the terminal for error messages. Common causes:
- Missing dependencies: `pip install -r requirements.txt`
- Database issues: Check if `mentalhealth.db` exists
- Port already in use: Change port with `--port 8001`

### Issue: Server runs but login still times out
**Solution:** 
- Check browser console (F12) for errors
- Check Network tab to see if request reaches backend
- Verify CORS settings in `backend/app/config.py`

### Issue: "Module not found" errors
**Solution:**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

## Test Login Endpoint Directly

Test if login works using curl:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=your_password"
```

If this works, the backend is fine and the issue is with frontend connection.

## Still Not Working?

1. **Check backend terminal** - Look for error messages
2. **Check browser console** - Press F12, look for errors
3. **Check Network tab** - See if request is being sent
4. **Restart both servers**:
   - Stop backend (Ctrl+C)
   - Stop frontend (Ctrl+C)
   - Start backend first
   - Then start frontend

## What I Fixed

I simplified the password verification code to avoid async issues that could cause timeouts. The login should now be faster and more reliable.

**Restart your backend server** for the fix to take effect!

