# XAI Feature Integration Guide

## 📍 Where Everything Was Added

### Backend Files Created

1. **`backend/app/xai_explainer.py`** (NEW FILE)
   - Location: `/backend/app/xai_explainer.py`
   - Purpose: Core XAI module with SHAP and LIME functionality
   - Key Classes: `XAIExplainer`

2. **`backend/app/routers/explain.py`** (NEW FILE)
   - Location: `/backend/app/routers/explain.py`
   - Purpose: API endpoints for explainability
   - Endpoints:
     - `GET /api/explain/global`
     - `POST /api/explain/local`
     - `GET /api/explain/health`

### Backend Files Modified

1. **`backend/app/main.py`**
   - Added import: `from app.routers import auth, datasets, training, predictions, admin, users, explain`
   - Added router: `app.include_router(explain.router, prefix="/api/explain", tags=["Explainability"])`
   - Location: Lines 6 and 60

2. **`backend/requirements.txt`**
   - Added: `lime==0.2.0.1`
   - Added: `matplotlib==3.8.2`
   - Location: End of file

### Frontend Files Created

1. **`frontend/app/explain/page.tsx`** (NEW FILE)
   - Location: `/frontend/app/explain/page.tsx`
   - Purpose: Explainability page UI
   - Route: `/explain`

### Frontend Files Modified

1. **`frontend/components/Nav.tsx`**
   - Added navigation link: `<Link href="/explain">Explainability</Link>`
   - Location: After "Test Model" link, before admin link

## 🚀 Quick Start

### 1. Install Backend Dependencies

```bash
cd backend
pip install lime==0.2.0.1 matplotlib==3.8.2
# Or reinstall all requirements
pip install -r requirements.txt
```

### 2. Restart Backend Server

```bash
cd backend
uvicorn app.main:app --reload
```

### 3. Frontend (No Changes Needed)

The frontend will automatically pick up the new route. Just navigate to `/explain` or click "Explainability" in the nav.

## 🧪 Testing

### Test Backend Endpoints

1. **Check Health:**
```bash
curl http://localhost:8000/api/explain/health
```

2. **Test Global Explanation:**
```bash
curl -X GET http://localhost:8000/api/explain/global \
  -H "Authorization: Bearer YOUR_TOKEN"
```

3. **Test Local Explanation:**
```bash
curl -X POST http://localhost:8000/api/explain/local \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel sad and anxious"}'
```

### Test Frontend

1. Navigate to `http://localhost:3000/explain`
2. Click "Explain Global Model Behavior"
3. Enter text and click "Explain This Prediction"

## 📋 Dummy JSON for Testing

### Global Explanation Response:
```json
{
  "feature_importance": [
    {"feature": "sad", "importance": 0.15},
    {"feature": "anxious", "importance": 0.12},
    {"feature": "depressed", "importance": 0.10}
  ],
  "summary_plot": "data:image/png;base64,iVBORw0KG...",
  "bar_plot": "data:image/png;base64,iVBORw0KG...",
  "model_type": "logistic_regression",
  "n_samples": 100
}
```

### Local Explanation Response:
```json
{
  "prediction": 1,
  "prediction_proba": {"class_0": 0.2, "class_1": 0.8},
  "feature_contributions": [
    {"feature": "sad", "shap_value": 0.15, "contribution": 0.15},
    {"feature": "anxious", "shap_value": 0.12, "contribution": 0.12}
  ],
  "force_plot": "data:image/png;base64,iVBORw0KG...",
  "waterfall_plot": "data:image/png;base64,iVBORw0KG...",
  "lime_explanation": {"explanation": "..."},
  "base_value": 0.5,
  "input_text": "I feel sad and anxious"
}
```

## ✅ Verification Checklist

- [ ] Backend dependencies installed (`lime`, `matplotlib`)
- [ ] Backend server restarts without errors
- [ ] `/api/explain/health` endpoint works
- [ ] Frontend page loads at `/explain`
- [ ] Navigation shows "Explainability" link
- [ ] Global explanation generates successfully
- [ ] Local explanation generates successfully
- [ ] Charts and plots display correctly

## 🔧 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'lime'"
**Solution:** Install LIME: `pip install lime==0.2.0.1`

### Issue: "No active model found"
**Solution:** Train a model first using the Training page

### Issue: "Failed to generate explanation"
**Solution:** 
- Check backend logs for detailed errors
- Ensure model file exists at `models/best_model.pkl`
- Verify SHAP is installed: `pip install shap==0.43.0`

### Issue: Frontend shows "No trained model found"
**Solution:** Train a model first, then refresh the explain page

## 📝 Notes

- The explainer automatically uses `best_model.pkl` if available
- Falls back to active model from database if `best_model.pkl` doesn't exist
- Global explanations may take 10-30 seconds (computing SHAP values)
- Local explanations are faster (2-5 seconds)
- All explanations include visual plots as base64 images

## 🎯 What Was NOT Changed

- ✅ No existing training logic modified
- ✅ No existing prediction endpoints modified
- ✅ No existing pages modified (only added new page)
- ✅ No database schema changes
- ✅ No breaking changes to existing functionality

## 📚 Additional Resources

- See `XAI_IMPLEMENTATION.md` for detailed documentation
- SHAP docs: https://shap.readthedocs.io/
- LIME docs: https://github.com/marcotcr/lime

