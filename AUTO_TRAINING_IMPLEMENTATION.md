# Multi-Model Auto Training & Auto-Selection Implementation

## Overview
This document describes the implementation of the new **Multi-Model Auto Training & Auto-Selection** feature that automatically trains multiple ML models, evaluates them, and selects the best performing model.

## 🎯 Features Implemented

### 1. **Automatic Multi-Model Training**
   - Trains 5 different ML models:
     - Logistic Regression
     - Random Forest
     - SVM (Support Vector Machine)
     - XGBoost
     - ANN (MLPClassifier - Multi-Layer Perceptron)

### 2. **Automatic Preprocessing**
   - Missing value handling
   - Categorical encoding
   - Text preprocessing and cleaning
   - Deduplication
   - PII anonymization (if enabled)
   - Train-test split (80/20)

### 3. **Model Evaluation**
   - Each model is evaluated using:
     - Accuracy
     - Precision
     - Recall
     - F1 Score
     - ROC-AUC (when applicable)
     - Confusion Matrix
     - Classification Report

### 4. **Best Model Selection**
   - Automatically selects the best model based on:
     - **Primary**: Highest F1 Score
     - **Fallback**: Highest Accuracy (if F1 scores are equal)

### 5. **Model Storage**
   - Saves `best_model.pkl` in `/models` directory
   - Saves all trained models in `/models/history` directory
   - Saves `metrics_report.json` with comprehensive metrics

### 6. **API Endpoints**

#### POST `/api/training/auto`
Triggers the full auto-training pipeline.

**Request:**
```json
{
  "dataset_id": 1,
  "use_smote": false
}
```

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "pending",
  "progress": 0.0,
  "message": "Auto-training started. Training multiple models..."
}
```

#### GET `/api/training/auto/{job_id}/results`
Get auto-training results for a specific job.

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "completed",
  "progress": 1.0,
  "message": "Auto-training completed",
  "best_model": "xgboost",
  "metrics": {
    "accuracy": 0.95,
    "precision": 0.94,
    "recall": 0.96,
    "f1": 0.95
  },
  "models_ranked": [
    {
      "model": "xgboost",
      "f1": 0.95,
      "accuracy": 0.95,
      "precision": 0.94,
      "recall": 0.96,
      "training_time": 45.2,
      "status": "success"
    },
    {
      "model": "random_forest",
      "f1": 0.93,
      "accuracy": 0.93,
      "precision": 0.92,
      "recall": 0.94,
      "training_time": 38.5,
      "status": "success"
    }
    // ... more models
  ]
}
```

#### GET `/api/training/metrics-report`
Download the metrics report JSON file.

### 7. **Frontend Updates**

#### New UI Components:
- **"Auto Train Models" Button**: Prominent button to start auto-training
- **Model Comparison Table**: Displays all models ranked by performance
- **Performance Charts**: Bar chart comparing F1 scores and accuracy
- **Download Report Button**: Download the metrics report JSON
- **Real-time Progress**: Shows training progress for each model
- **Best Model Highlighting**: Visual indicator for the selected best model

## 📁 Files Modified/Created

### Backend Files

1. **`backend/app/auto_trainer.py`** (NEW)
   - Contains all auto-training logic:
     - `preprocess_data()`: Comprehensive data preprocessing
     - `train_multiple_models()`: Trains all 5 models
     - `evaluate_models()`: Evaluates and compares models
     - `select_best_model()`: Selects best model based on F1 score
     - `save_model_and_report()`: Saves models and metrics report

2. **`backend/app/routers/training.py`** (MODIFIED)
   - Added `auto_train_models_async()`: Background function for auto-training
   - Added `POST /auto` endpoint: Start auto-training
   - Added `GET /auto/{job_id}/results` endpoint: Get auto-training results
   - Added `GET /metrics-report` endpoint: Download metrics report

3. **`backend/app/schemas.py`** (MODIFIED)
   - Added `AutoTrainingRequest` schema
   - Added `AutoTrainingResponse` schema

4. **`backend/requirements.txt`** (MODIFIED)
   - Added `xgboost==2.0.3`

### Frontend Files

1. **`frontend/app/training/page.tsx`** (MODIFIED)
   - Added "Auto Train Models" button
   - Added model comparison table
   - Added performance charts
   - Added download report functionality
   - Added real-time progress tracking for auto-training jobs

## 🔧 Installation & Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This will install `xgboost` along with other dependencies.

### 2. Create Required Directories

The system will automatically create:
- `/models` directory (if it doesn't exist)
- `/models/history` directory (if it doesn't exist)

### 3. Run the Application

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm run dev
```

## 📊 Usage Example

### Starting Auto-Training

1. Navigate to the Training page
2. Select a dataset from the dropdown
3. Optionally check "Use SMOTE" for imbalanced data
4. Click **"🚀 Auto Train Models"** button
5. The system will:
   - Train 5 models sequentially
   - Show progress updates
   - Display model comparison table when complete
   - Highlight the best model

### Viewing Results

- The training jobs list will show auto-training jobs with an "AUTO" badge
- Click on a completed auto-training job to see:
  - Model comparison table
  - Performance charts
  - Best model indicator
  - Download report button

### Downloading Metrics Report

Click the "📥 Download Report" button to download `metrics_report.json` containing:
- All model metrics
- Preprocessing information
- Model rankings
- Training times

## 📝 Metrics Report Structure

```json
{
  "timestamp": "20241120_123456",
  "dataset_id": 1,
  "preprocessing_info": {
    "initial_rows": 1000,
    "missing_values_handled": 10,
    "duplicates_removed": 5,
    "final_rows": 985,
    "class_distribution": {
      "0": 492,
      "1": 493
    }
  },
  "best_model": "xgboost",
  "best_model_metrics": {
    "accuracy": 0.95,
    "precision": 0.94,
    "recall": 0.96,
    "f1": 0.95,
    "roc_auc": 0.97
  },
  "all_models_metrics": {
    "logistic_regression": {
      "metrics": {...},
      "training_time": 12.5,
      "status": "success"
    },
    // ... other models
  },
  "models_ranked": [
    {
      "model": "xgboost",
      "f1": 0.95,
      "accuracy": 0.95,
      "training_time": 45.2
    }
    // ... ranked models
  ]
}
```

## 🎨 UI Features

### Model Comparison Table
- Shows all 5 models ranked by performance
- Displays F1 Score, Accuracy, Precision, Recall, and Training Time
- Highlights the best model with a green background and ⭐ icon
- Responsive design for mobile and desktop

### Performance Charts
- Bar chart comparing F1 scores across models
- Bar chart comparing accuracy across models
- Interactive tooltips showing exact values

### Real-time Progress
- Shows current model being trained
- Displays overall progress percentage
- Updates every 5 seconds

## 🔍 Technical Details

### Model Configurations

1. **Logistic Regression**
   - TF-IDF vectorization (max_features=5000, ngram_range=(1,2))
   - Max iterations: 1000

2. **Random Forest**
   - TF-IDF vectorization
   - 100 estimators
   - Parallel processing enabled

3. **SVM**
   - TF-IDF vectorization
   - StandardScaler (sparse matrix compatible)
   - RBF kernel
   - Probability estimates enabled

4. **XGBoost**
   - TF-IDF vectorization
   - 100 estimators
   - Max depth: 6
   - Learning rate: 0.1

5. **ANN (MLPClassifier)**
   - TF-IDF vectorization
   - StandardScaler
   - Hidden layers: (100, 50)
   - Early stopping enabled
   - Max iterations: 500

### Best Model Selection Logic

```python
# Primary criterion: Highest F1 Score
# Fallback: Highest Accuracy (if F1 scores are equal)
best_model = model with highest F1 score
if tie:
    best_model = model with highest accuracy
```

## 🚀 Future Enhancements

Potential improvements:
1. Add SHAP feature importance visualization (requires model-specific implementation)
2. Add hyperparameter tuning for each model
3. Add cross-validation for more robust evaluation
4. Add model ensemble option
5. Add export to different formats (CSV, PDF)
6. Add model comparison export functionality

## ⚠️ Notes

- **SMOTE**: Currently, SMOTE is not applied in auto-training (complex to implement with pipelines). Use individual model training with SMOTE if needed.
- **Training Time**: Auto-training takes longer than single model training as it trains 5 models sequentially.
- **Resource Usage**: XGBoost and ANN models may require more memory and CPU resources.
- **Model Storage**: All models are saved in `/models/history` for future reference.

## 📞 Support

For issues or questions:
1. Check the training job error messages
2. Review the metrics report for detailed information
3. Check backend logs for debugging information

---

**Implementation Date**: November 2024
**Version**: 1.0.0

