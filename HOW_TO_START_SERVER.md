# 🚀 HOW TO START THE BACKEND SERVER

## ✅ GOOD NEWS: Backend Code Works!

I tested it - the server starts and works perfectly. You just need to **start it**.

## 🎯 EASIEST WAY: Double-Click Method

1. **Open Finder**
2. **Navigate to:** `backend` folder
3. **Find file:** `START_HERE.command`
4. **Double-click it**
5. **A terminal window will open** - keep it open!
6. **Wait for:** `INFO: Uvicorn running on http://0.0.0.0:8000`

## ✅ Verify It's Working

Open browser: `http://localhost:8000/api/health`

Should see: `{"status":"healthy","version":"1.0.0"}`

## ✅ Then Try Login

Once you see the server running, go back to your login page!

---

## 🔧 Alternative: Terminal Method

If double-click doesn't work:

1. **Open Terminal** (Cmd+Space, type "Terminal")
2. **Copy and paste these commands:**

```bash
cd "/Users/karthikkukkala/Desktop/Degital mental Health /backend"
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

3. **Keep terminal open** - don't close it!

---

## ⚠️ IMPORTANT

- **The terminal window MUST stay open**
- **Don't close it** - closing stops the server
- **You'll see server logs** in that window
- **Press Ctrl+C** to stop when done

---

## ✅ What Success Looks Like

When server is running, you'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

And `http://localhost:8000/api/health` will show:
```json
{"status":"healthy","version":"1.0.0"}
```

---

## 🐛 If It Still Doesn't Work

**Check the terminal for error messages** and share them with me.

The backend code is fine - it just needs to be running!

