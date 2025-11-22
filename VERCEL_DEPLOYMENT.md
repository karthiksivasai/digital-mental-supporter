# Vercel Deployment Guide

## ✅ Configuration Complete

The project has been configured for Vercel deployment with:
- `vercel.json` - Root directory configuration
- Updated `next.config.js` - Removed standalone output for Vercel compatibility

## 🚀 Deployment Steps

### 1. Automatic Deployment (Recommended)
If you've connected your GitHub repository to Vercel, it will automatically deploy when you push to `main` branch.

**Current Status:** ✅ Code pushed to GitHub - Vercel should auto-deploy

### 2. Manual Configuration in Vercel Dashboard (REQUIRED)

**IMPORTANT:** You MUST configure the Root Directory in Vercel Dashboard:

1. **Go to Vercel Project Settings:**
   - Visit: https://vercel.com/karthiksivasai/digital-mental-supporter/settings/general

2. **Set Root Directory (CRITICAL STEP):**
   - Scroll to "Root Directory" section
   - Click "Edit"
   - Set to: `frontend`
   - Click "Save"
   - **This step is REQUIRED - vercel.json cannot set rootDirectory**

3. **Verify Build Settings:**
   - Go to "Build & Development Settings"
   - Framework Preset: `Next.js` (should auto-detect)
   - Build Command: `npm run build` (default - vercel.json will override)
   - Output Directory: `.next` (default - vercel.json will override)
   - Install Command: `npm install` (default - vercel.json will override)

### 3. Environment Variables

**Important:** Set these in Vercel → Settings → Environment Variables:

1. **NEXT_PUBLIC_API_URL**
   - **Value:** Your backend API URL
   - **Options:**
     - If backend is deployed: `https://your-backend-url.com`
     - If using local backend: `http://localhost:8000` (won't work in production)
     - If backend is on another platform: Use that URL

**Example:**
```
NEXT_PUBLIC_API_URL=https://your-backend-api.herokuapp.com
```

### 4. Check Deployment Status

1. Go to: https://vercel.com/karthiksivasai/digital-mental-supporter
2. Check the latest deployment
3. View build logs if deployment fails

## 🔍 Troubleshooting

### Issue: 404 NOT_FOUND Error
**Solution:** 
- Verify Root Directory is set to `frontend` in Vercel settings
- Check that `vercel.json` exists in repository root
- Ensure build completed successfully

### Issue: Build Fails
**Check:**
- Build logs in Vercel dashboard
- Ensure `package.json` exists in `frontend/` directory
- Check Node.js version (should be 18.x or 20.x)

### Issue: API Calls Fail
**Solution:**
- Set `NEXT_PUBLIC_API_URL` environment variable
- Ensure backend CORS allows your Vercel domain
- Check backend is running and accessible

### Issue: Environment Variables Not Working
**Solution:**
- Variables must start with `NEXT_PUBLIC_` to be accessible in browser
- Redeploy after adding environment variables
- Check variable names match exactly

## 📋 Current Configuration

- **Root Directory:** `frontend` (configured in `vercel.json`)
- **Framework:** Next.js 14
- **Build Command:** `npm run build`
- **Output Directory:** `.next`

## 🔗 Useful Links

- **Vercel Dashboard:** https://vercel.com/karthiksivasai/digital-mental-supporter
- **GitHub Repository:** https://github.com/karthiksivasai/digital-mental-supporter
- **Vercel Docs:** https://vercel.com/docs

## ✅ Next Steps

1. ✅ Code pushed to GitHub
2. ⏳ Wait for Vercel auto-deployment (or trigger manually)
3. ⏳ Set `NEXT_PUBLIC_API_URL` environment variable
4. ⏳ Verify deployment is successful
5. ⏳ Test the deployed application

## 🎯 Expected Result

After successful deployment, your app should be accessible at:
- **Production URL:** `https://digital-mental-supporter.vercel.app`
- **Preview URLs:** Generated for each branch/PR

---

**Note:** The backend API needs to be deployed separately (not on Vercel). Consider deploying backend to:
- Railway
- Render
- Heroku
- AWS/GCP/Azure
- Or keep running locally for development

