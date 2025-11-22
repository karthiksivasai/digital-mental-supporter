# Fix Sign-In Issue - Step by Step

## The Problem
You can't sign in after adding the XAI feature. The code is correct, but the server might not be running properly.

## Step-by-Step Fix

### Step 1: Check if Server is Running

Open a **NEW terminal** and run:
```bash
curl http://localhost:8000/api/health
```

**Expected Result:**
- ✅ `{"status":"healthy","version":"1.0.0"}` → Server is running
- ❌ `Connection refused` → Server is NOT running

### Step 2: Stop ALL Running Servers

Find ALL terminals running the backend server:
1. Look for terminals showing `uvicorn app.main:app`
2. In each terminal, press `Ctrl+C` to stop it
3. Make sure ALL are stopped

### Step 3: Start Fresh Server

Open a **NEW terminal** and run:
```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
INFO:     Started reloader process
```

**If you see errors:**
- Check the error message
- Make sure you're in the virtual environment
- Try: `pip install -r requirements.txt`

### Step 4: Verify Server is Working

In a **NEW terminal** (keep server running), test:
```bash
curl http://localhost:8000/api/health
```

Should return: `{"status":"healthy","version":"1.0.0"}`

### Step 5: Test Login Endpoint

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
source venv/bin/activate
python test_login.py
```

Or manually:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=YOUR_EMAIL&password=YOUR_PASSWORD"
```

### Step 6: Check Frontend Connection

1. Open browser console (F12)
2. Go to Network tab
3. Try to login
4. Check if request reaches `http://localhost:8000/api/auth/login`

**If you see:**
- ✅ Request shows up → Frontend is connecting
- ❌ No request → Frontend can't reach backend

### Step 7: Check Frontend API URL

Check `frontend/.env` or `frontend/next.config.js`:
```bash
cd frontend
cat .env.local 2>/dev/null || cat .env 2>/dev/null || echo "No .env file"
```

Should have:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Common Issues & Solutions

### Issue: "Connection refused"
**Solution:** Backend server is not running. Follow Step 2-3.

### Issue: Server starts but crashes
**Solution:** Check terminal for error messages. Common fixes:
- `pip install -r requirements.txt`
- Check database file exists: `ls backend/mentalhealth.db`

### Issue: "Port already in use"
**Solution:** 
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill
# Or use different port
uvicorn app.main:app --reload --port 8001
```

### Issue: Frontend can't connect
**Solution:**
1. Check `NEXT_PUBLIC_API_URL` in frontend
2. Make sure backend is running on same port
3. Check CORS settings in `backend/app/config.py`

### Issue: Login times out
**Solution:**
1. Make sure server is actually running (Step 1)
2. Check server terminal for errors
3. Try restarting both frontend and backend

## Quick Verification Checklist

- [ ] Backend server is running (`curl http://localhost:8000/api/health` works)
- [ ] No errors in backend terminal
- [ ] Frontend can reach backend (check Network tab)
- [ ] API URL is correct in frontend config
- [ ] Database file exists (`backend/mentalhealth.db`)

## Still Not Working?

1. **Check backend terminal** - Look for any error messages
2. **Check browser console** - Press F12, look for errors
3. **Check Network tab** - See if requests are being sent
4. **Try incognito mode** - Rule out browser cache issues
5. **Restart everything**:
   - Stop backend (Ctrl+C)
   - Stop frontend (Ctrl+C)  
   - Start backend first
   - Then start frontend

## Test Script

I've created `backend/test_login.py` to help test the login endpoint.

Run it with:
```bash
cd backend
source venv/bin/activate
python test_login.py
```

Update the credentials in the script first!

