"""
Auto Training Module for Multi-Model Training and Selection
"""
import os
import json
import pandas as pd
import numpy as np
import joblib
import time
from typing import Dict, List, Tuple, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from imblearn.over_sampling import SMOTE
from datetime import datetime
try:
    import xgboost as xgb
except ImportError:
    xgb = None  # XGBoost is optional
from app.ml_pipeline import MLPipeline


def preprocess_data(
    df: pd.DataFrame,
    text_column: str,
    label_column: str,
    is_anonymous: bool = False
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Comprehensive data preprocessing
    
    Returns:
        X: Features array
        y: Labels array
        preprocessing_info: Dictionary with preprocessing statistics
    """
    preprocessing_info = {
        "initial_rows": len(df),
        "missing_values_handled": 0,
        "duplicates_removed": 0,
        "outliers_handled": 0,
        "final_rows": 0
    }
    
    # Use existing MLPipeline for consistency
    pipeline = MLPipeline()
    
    # Anonymize if needed
    if is_anonymous:
        df = pipeline.anonymize_pii(df, text_column)
    
    # Handle missing values
    initial_len = len(df)
    df = pipeline.handle_missing_values(df, text_column, label_column)
    preprocessing_info["missing_values_handled"] = initial_len - len(df)
    
    # Deduplicate
    initial_len = len(df)
    df = pipeline.deduplicate(df, text_column)
    preprocessing_info["duplicates_removed"] = initial_len - len(df)
    
    # Preprocess text
    df[text_column] = df[text_column].apply(pipeline.preprocess_text)
    
    # Extract features and labels
    X = df[text_column].values
    y = df[label_column].values
    
    # Ensure labels are binary (0/1)
    if y.dtype != 'int':
        y_series = pd.Series(y)
        y_series = pd.to_numeric(y_series, errors='coerce').fillna(0)
        y = y_series.astype(int).values
    
    # Ensure binary labels (0/1)
    unique_labels = np.unique(y)
    if len(unique_labels) < 2:
        raise ValueError("Dataset must contain at least 2 classes")
    
    if len(unique_labels) == 2:
        if not np.array_equal(unique_labels, [0, 1]):
            y = np.where(y == unique_labels[0], 0, 1)
    elif len(unique_labels) > 2:
        y = np.where(y == unique_labels[0], 0, 1)
    
    preprocessing_info["final_rows"] = len(X)
    preprocessing_info["class_distribution"] = {
        int(label): int(count) for label, count in zip(*np.unique(y, return_counts=True))
    }
    
    return X, y, preprocessing_info


def train_multiple_models(
    X_train: np.ndarray,
    y_train: np.ndarray,
    X_test: np.ndarray,
    y_test: np.ndarray,
    use_smote: bool = False,
    progress_callback: Optional[callable] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Train multiple ML models
    
    Returns:
        Dictionary with model_name as key and dict containing:
        - model: trained model
        - pipeline: sklearn pipeline
        - metrics: evaluation metrics
        - training_time: time taken to train
    """
    models_config = {
        "logistic_regression": {
            "pipeline": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('classifier', LogisticRegression(max_iter=1000, random_state=42))
            ])
        },
        "random_forest": {
            "pipeline": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('classifier', RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))
            ])
        },
        "svm": {
            "pipeline": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('scaler', StandardScaler(with_mean=False)),  # Sparse matrix compatible
                ('classifier', SVC(kernel='rbf', probability=True, random_state=42))
            ])
        },
        "xgboost": {
            "pipeline": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('classifier', xgb.XGBClassifier(
                    n_estimators=100,
                    max_depth=6,
                    learning_rate=0.1,
                    random_state=42,
                    n_jobs=-1,
                    eval_metric='logloss'
                ))
            ]) if xgb is not None else None
        },
        "ann": {
            "pipeline": Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('scaler', StandardScaler(with_mean=False)),
                ('classifier', MLPClassifier(
                    hidden_layer_sizes=(100, 50),
                    max_iter=500,
                    random_state=42,
                    early_stopping=True,
                    validation_fraction=0.1
                ))
            ])
        }
    }
    
    results = {}
    
    # Train each model
    for idx, (model_name, config) in enumerate(models_config.items()):
        # Skip models with None pipeline (e.g., xgboost when not installed)
        if config["pipeline"] is None:
            if progress_callback:
                progress_callback(f"Skipping {model_name} (not available)...")
            results[model_name] = {
                "error": f"{model_name} is not available (missing dependencies)",
                "metrics": {
                    'accuracy': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0
                },
                "training_time": 0.0
            }
            continue
            
        if progress_callback:
            progress_callback(f"Training {model_name}... ({idx+1}/{len(models_config)})")
        
        start_time = time.time()
        # Create a fresh pipeline instance
        pipeline = Pipeline(config["pipeline"].steps)
        
        try:
            # Train the pipeline
            pipeline.fit(X_train, y_train)
            
            # Evaluate
            y_pred = pipeline.predict(X_test)
            y_pred_proba = None
            try:
                y_pred_proba = pipeline.predict_proba(X_test)[:, 1]
            except:
                pass
            
            # Calculate metrics
            metrics = {
                'accuracy': float(accuracy_score(y_test, y_pred)),
                'precision': float(precision_score(y_test, y_pred, average='weighted', zero_division=0)),
                'recall': float(recall_score(y_test, y_pred, average='weighted', zero_division=0)),
                'f1': float(f1_score(y_test, y_pred, average='weighted', zero_division=0)),
            }
            
            if y_pred_proba is not None and len(np.unique(y_test)) > 1:
                try:
                    metrics['roc_auc'] = float(roc_auc_score(y_test, y_pred_proba))
                except:
                    metrics['roc_auc'] = 0.0
            
            metrics['confusion_matrix'] = confusion_matrix(y_test, y_pred).tolist()
            metrics['classification_report'] = classification_report(y_test, y_pred, output_dict=True)
            
            training_time = time.time() - start_time
            
            results[model_name] = {
                "model": pipeline.named_steps['classifier'],
                "pipeline": pipeline,
                "vectorizer": pipeline.named_steps.get('tfidf'),
                "metrics": metrics,
                "training_time": training_time
            }
            
        except Exception as e:
            # If a model fails, log error but continue with others
            results[model_name] = {
                "error": str(e),
                "metrics": {
                    'accuracy': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1': 0.0
                },
                "training_time": 0.0
            }
    
    return results


def evaluate_models(models_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate and compare all trained models
    
    Returns:
        Dictionary with evaluation summary
    """
    evaluation = {
        "models": {},
        "best_model": None,
        "best_f1": 0.0,
        "best_accuracy": 0.0
    }
    
    for model_name, result in models_results.items():
        if "error" in result:
            evaluation["models"][model_name] = {
                "status": "failed",
                "error": result["error"],
                "metrics": result["metrics"]
            }
            continue
        
        metrics = result["metrics"]
        evaluation["models"][model_name] = {
            "status": "success",
            "metrics": metrics,
            "training_time": result["training_time"]
        }
        
        # Track best model by F1 score (fallback to accuracy)
        f1 = metrics.get('f1', 0.0)
        accuracy = metrics.get('accuracy', 0.0)
        
        if f1 > evaluation["best_f1"] or (f1 == evaluation["best_f1"] and accuracy > evaluation["best_accuracy"]):
            evaluation["best_f1"] = f1
            evaluation["best_accuracy"] = accuracy
            evaluation["best_model"] = model_name
    
    return evaluation


def select_best_model(
    models_results: Dict[str, Dict[str, Any]],
    evaluation: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """
    Select the best model based on F1 score (fallback to accuracy)
    
    Returns:
        Tuple of (best_model_name, best_model_result)
    """
    best_model_name = evaluation["best_model"]
    
    if not best_model_name or best_model_name not in models_results:
        # Fallback: find model with highest F1
        best_f1 = -1
        best_model_name = None
        for name, result in models_results.items():
            if "error" not in result:
                f1 = result["metrics"].get('f1', 0.0)
                if f1 > best_f1:
                    best_f1 = f1
                    best_model_name = name
        
        if not best_model_name:
            raise ValueError("No successful model found")
    
    return best_model_name, models_results[best_model_name]


def save_model_and_report(
    best_model_name: str,
    best_model_result: Dict[str, Any],
    all_models_results: Dict[str, Dict[str, Any]],
    evaluation: Dict[str, Any],
    preprocessing_info: Dict[str, Any],
    dataset_id: int,
    models_dir: str = "models",
    history_dir: str = "models/history"
) -> Dict[str, str]:
    """
    Save best model, all models to history, and metrics report
    
    Returns:
        Dictionary with paths to saved files
    """
    os.makedirs(models_dir, exist_ok=True)
    os.makedirs(history_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save best model as best_model.pkl
    best_model_path = os.path.join(models_dir, "best_model.pkl")
    best_pipeline = best_model_result["pipeline"]
    
    joblib.dump({
        'pipeline': best_pipeline,
        'vectorizer': best_model_result.get("vectorizer"),
        'model': best_model_result["model"],
        'model_type': best_model_name,
        'version': f"best_{timestamp}",
        'metadata': {
            "dataset_id": dataset_id,
            "training_date": datetime.now().isoformat(),
            "metrics": best_model_result["metrics"],
            "preprocessing_info": preprocessing_info
        },
        'saved_at': datetime.now().isoformat()
    }, best_model_path)
    
    # Save all models to history
    history_paths = {}
    for model_name, result in all_models_results.items():
        if "error" not in result:
            history_model_path = os.path.join(history_dir, f"{model_name}_{timestamp}.pkl")
            joblib.dump({
                'pipeline': result["pipeline"],
                'vectorizer': result.get("vectorizer"),
                'model': result["model"],
                'model_type': model_name,
                'version': f"{model_name}_{timestamp}",
                'metadata': {
                    "dataset_id": dataset_id,
                    "training_date": datetime.now().isoformat(),
                    "metrics": result["metrics"],
                    "preprocessing_info": preprocessing_info
                },
                'saved_at': datetime.now().isoformat()
            }, history_model_path)
            history_paths[model_name] = history_model_path
    
    # Save metrics report
    report_path = os.path.join(models_dir, "metrics_report.json")
    report = {
        "timestamp": timestamp,
        "dataset_id": dataset_id,
        "preprocessing_info": preprocessing_info,
        "best_model": best_model_name,
        "best_model_metrics": best_model_result["metrics"],
        "all_models_metrics": {
            name: {
                "metrics": result.get("metrics", {}),
                "training_time": result.get("training_time", 0.0),
                "status": "success" if "error" not in result else "failed",
                "error": result.get("error") if "error" in result else None
            }
            for name, result in all_models_results.items()
        },
        "evaluation_summary": evaluation,
        "models_ranked": sorted(
            [
                {
                    "model": name,
                    "f1": result.get("metrics", {}).get("f1", 0.0),
                    "accuracy": result.get("metrics", {}).get("accuracy", 0.0),
                    "training_time": result.get("training_time", 0.0)
                }
                for name, result in all_models_results.items()
                if "error" not in result
            ],
            key=lambda x: (x["f1"], x["accuracy"]),
            reverse=True
        )
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return {
        "best_model_path": best_model_path,
        "report_path": report_path,
        "history_paths": history_paths
    }

