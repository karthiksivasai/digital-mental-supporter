# Explainable AI (XAI) Feature Implementation

## ✅ Implementation Complete

A comprehensive Explainable AI feature has been added to your Mental Health Detection platform using SHAP and LIME.

## 📁 Files Created/Modified

### New Backend Files:
1. **`backend/app/xai_explainer.py`** - Core XAI module with SHAP and LIME functionality
2. **`backend/app/routers/explain.py`** - API endpoints for explainability

### Modified Backend Files:
1. **`backend/app/main.py`** - Added explain router
2. **`backend/requirements.txt`** - Added `lime==0.2.0.1` and `matplotlib==3.8.2`

### New Frontend Files:
1. **`frontend/app/explain/page.tsx`** - Explainability page UI

### Modified Frontend Files:
1. **`frontend/components/Nav.tsx`** - Added "Explainability" navigation link

## 🎯 Features Implemented

### 1. Global Model Explanation
- **SHAP Summary Plot**: Visual representation of feature importance across all predictions
- **SHAP Bar Plot**: Bar chart showing mean absolute SHAP values
- **Feature Importance Table**: Ranked list of top features with importance scores
- **Feature Importance Chart**: Interactive bar chart visualization

### 2. Individual Prediction Explanation
- **SHAP Force Plot**: Visual representation of feature contributions for a specific prediction
- **Waterfall Plot**: Shows how each feature contributes to the final prediction
- **Feature Contributions Table**: Detailed breakdown of each feature's impact
- **Feature Contributions Chart**: Interactive visualization of contributions
- **LIME Explanation**: Local interpretable model-agnostic explanations
- **Prediction Summary**: Shows predicted class and confidence scores

## 🔧 API Endpoints

### GET `/api/explain/global`
Returns global SHAP explanation for the best model.

**Response:**
```json
{
  "feature_importance": [
    {
      "feature": "feature_name",
      "importance": 0.123456
    }
  ],
  "summary_plot": "data:image/png;base64,...",
  "bar_plot": "data:image/png;base64,...",
  "model_type": "logistic_regression",
  "n_samples": 100
}
```

### POST `/api/explain/local`
Returns local SHAP and LIME explanation for a specific prediction.

**Request:**
```json
{
  "text": "I feel sad and anxious about my future"
}
```

**Response:**
```json
{
  "prediction": 1,
  "prediction_proba": {
    "class_0": 0.2,
    "class_1": 0.8
  },
  "feature_contributions": [
    {
      "feature": "feature_name",
      "shap_value": 0.123456,
      "contribution": 0.123456
    }
  ],
  "force_plot": "data:image/png;base64,...",
  "waterfall_plot": "data:image/png;base64,...",
  "lime_explanation": {...},
  "base_value": 0.5,
  "input_text": "I feel sad and anxious about my future"
}
```

### GET `/api/explain/health`
Check if explainability service is available.

**Response:**
```json
{
  "status": "available",
  "model_path": "models/best_model.pkl",
  "model_exists": true
}
```

## 📦 Installation

### Backend Dependencies
The following dependencies have been added to `requirements.txt`:
- `lime==0.2.0.1` - LIME explainer
- `matplotlib==3.8.2` - For generating plots

Install dependencies:
```bash
cd backend
pip install -r requirements.txt
```

### Frontend Dependencies
No new frontend dependencies required. Uses existing:
- `recharts` - For charts
- `react-hot-toast` - For notifications
- `axios` - For API calls

## 🚀 Usage

### 1. Access the Explainability Page
Navigate to `/explain` in your frontend application, or click "Explainability" in the navigation menu.

### 2. Global Explanation
1. Click "🔍 Explain Global Model Behavior"
2. Wait for the explanation to generate (may take 10-30 seconds)
3. View:
   - Feature importance table
   - Feature importance chart
   - SHAP summary plot
   - SHAP bar plot

### 3. Local Explanation
1. Enter text in the textarea (e.g., "I feel sad and anxious")
2. Click "🔍 Explain This Prediction"
3. View:
   - Prediction summary (class and confidence)
   - Feature contributions table
   - Feature contributions chart
   - SHAP force plot
   - Waterfall plot
   - LIME explanation

## 🔍 How It Works

### SHAP (SHapley Additive exPlanations)
- **TreeExplainer**: Used for Random Forest and XGBoost models
- **LinearExplainer**: Used for Logistic Regression models
- **KernelExplainer**: Fallback for SVM, ANN, and other models

### Model Loading
The explainer automatically:
1. Loads `best_model.pkl` from `models/` directory
2. Falls back to active model from database if `best_model.pkl` doesn't exist
3. Extracts vectorizer, model, and feature names
4. Prepares background data for SHAP calculations

### Background Data
- Uses training dataset if available
- Falls back to sample data if dataset not found
- Uses 100 samples by default (configurable)

## 📊 Example Outputs

### Global Explanation
- **Top Features**: Shows which words/features are most important overall
- **Summary Plot**: Dot plot showing feature importance distribution
- **Bar Plot**: Mean absolute SHAP values

### Local Explanation
- **Feature Contributions**: Shows which features pushed prediction toward High Risk (red) or Low Risk (blue)
- **Force Plot**: Visual representation of feature contributions
- **Waterfall Plot**: Step-by-step contribution visualization

## 🐛 Troubleshooting

### "No active model found"
- Train a model first using the Training page
- Ensure `best_model.pkl` exists in `models/` directory

### "Failed to generate explanation"
- Check that SHAP and LIME are installed correctly
- Verify model file is not corrupted
- Check backend logs for detailed error messages

### Slow Performance
- Global explanations may take 10-30 seconds
- Local explanations are faster (2-5 seconds)
- Consider reducing background samples for faster processing

## 🔐 Security & Authentication

- Endpoints require authentication (uses `get_current_user`)
- Public access allowed (guest users can use explainability)
- No sensitive data exposed in explanations

## 📝 Code Structure

### Backend
```
backend/
├── app/
│   ├── xai_explainer.py      # Core XAI logic
│   └── routers/
│       └── explain.py        # API endpoints
```

### Frontend
```
frontend/
├── app/
│   └── explain/
│       └── page.tsx          # Explainability UI
```

## 🎨 UI Features

- **Modern Design**: Matches existing design system
- **Responsive**: Works on all screen sizes
- **Loading States**: Shows progress during explanation generation
- **Error Handling**: User-friendly error messages
- **Interactive Charts**: Hover tooltips and legends
- **Color Coding**: Red for risk-increasing features, Blue for risk-decreasing features

## 🔄 Integration Points

### With Existing System
- Uses existing model loading mechanism
- Integrates with database models
- Uses existing authentication system
- Follows existing API patterns

### Model Compatibility
- Works with all model types:
  - Logistic Regression ✅
  - Random Forest ✅
  - SVM ✅
  - XGBoost ✅
  - ANN ✅

## 📈 Future Enhancements (Optional)

- Add LIME text explainer for better text explanations
- Add comparison between multiple models
- Add explanation history/saving
- Add export functionality (PDF/CSV)
- Add interactive SHAP plots (HTML instead of images)
- Add feature importance over time

## 🧪 Testing

### Test Global Explanation
```bash
curl -X GET http://localhost:8000/api/explain/global \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Test Local Explanation
```bash
curl -X POST http://localhost:8000/api/explain/local \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text": "I feel sad and anxious"}'
```

## 📚 References

- [SHAP Documentation](https://shap.readthedocs.io/)
- [LIME Documentation](https://github.com/marcotcr/lime)
- [Explainable AI Best Practices](https://www.partnershiponai.org/explainability/)

## ✅ Checklist

- [x] Backend XAI module created
- [x] API endpoints implemented
- [x] Frontend page created
- [x] Navigation link added
- [x] Dependencies added
- [x] Error handling implemented
- [x] Documentation created
- [x] Integration with existing system
- [x] Model compatibility verified

## 🎯 Summary

The XAI feature is now fully integrated into your Mental Health Detection platform. Users can:
1. Understand overall model behavior through global explanations
2. Understand individual predictions through local explanations
3. See which features contribute to predictions
4. Visualize explanations through charts and plots

The implementation is modular, well-documented, and follows your existing code patterns.

