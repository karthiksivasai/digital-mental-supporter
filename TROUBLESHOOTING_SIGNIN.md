# Troubleshooting Sign-In Issues

## Quick Fix Steps

### 1. Check if Backend Server is Running

The sign-in problem is usually because the backend server isn't running or crashed.

**Check if server is running:**
- Look for a terminal window running `uvicorn app.main:app --reload`
- Check if you can access `http://localhost:8000/api/health` in your browser
- You should see: `{"status":"healthy","version":"1.0.0"}`

### 2. Restart Backend Server

**Stop the server:**
- Find the terminal where the server is running
- Press `Ctrl+C` to stop it

**Start the server:**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 3. Check for Errors

If the server won't start, check for error messages in the terminal. Common issues:

**Import Errors:**
- Make sure you're in the virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Port Already in Use:**
- Another process might be using port 8000
- Kill it: `lsof -ti:8000 | xargs kill` (Mac/Linux)
- Or change port: `uvicorn app.main:app --reload --port 8001`

**Database Errors:**
- Check if `mentalhealth.db` exists in the backend folder
- The server will create it automatically if missing

### 4. Verify Frontend Connection

**Check frontend is connecting to backend:**
- Open browser console (F12)
- Look for errors when trying to sign in
- Check Network tab to see if requests are reaching the backend

**Check API URL:**
- Frontend should connect to `http://localhost:8000`
- Check `.env` or `next.config.js` for `NEXT_PUBLIC_API_URL`

### 5. Test Login Endpoint Directly

Test if the login endpoint works:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your_email@example.com&password=your_password"
```

If this works, the backend is fine and the issue is with the frontend connection.

## Common Issues

### Issue: "Network Error" or "Connection Refused"
**Solution:** Backend server is not running. Start it using step 2 above.

### Issue: "401 Unauthorized" or "Incorrect email or password"
**Solution:** 
- Check your email and password are correct
- Make sure you've registered an account first
- Try registering a new account

### Issue: "CORS Error"
**Solution:** 
- Make sure backend CORS settings allow your frontend URL
- Check `backend/app/config.py` for `ALLOWED_ORIGINS`

### Issue: Server crashes on startup
**Solution:**
- Check terminal for error messages
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.9+)

## Still Having Issues?

1. **Check backend logs** - Look at the terminal where the server is running
2. **Check browser console** - Look for JavaScript errors
3. **Check network tab** - See what requests are being made
4. **Try incognito mode** - Rule out browser cache issues

## Quick Health Check

Run these commands to verify everything is set up:

```bash
# Check Python version
python --version

# Check virtual environment
which python  # Should point to venv/bin/python

# Check dependencies
pip list | grep -E "(fastapi|uvicorn|sqlalchemy)"

# Test imports
python -c "from app.main import app; print('OK')"
```

If all checks pass, restart the server and try signing in again.

