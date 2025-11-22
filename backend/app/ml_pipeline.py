import pandas as pd
import numpy as np
import joblib
import re
from typing import Dict, List, Tuple, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, classification_report
)
from imblearn.over_sampling import SMOTE
import os
from datetime import datetime


class MLPipeline:
    def __init__(self, model_type: str = "logistic_regression"):
        self.model_type = model_type
        self.pipeline = None
        self.vectorizer = None
        self.model = None
        self.feature_names = None
        
    def preprocess_text(self, text: str) -> str:
        """Basic text cleaning"""
        if pd.isna(text):
            return ""
        text = str(text).lower()
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def anonymize_pii(self, df: pd.DataFrame, text_column: str) -> pd.DataFrame:
        """Remove PII columns if present"""
        pii_keywords = ['name', 'email', 'phone', 'address', 'ssn', 'id']
        columns_to_drop = []
        for col in df.columns:
            if any(keyword in col.lower() for keyword in pii_keywords):
                columns_to_drop.append(col)
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
        return df
    
    def handle_missing_values(self, df: pd.DataFrame, text_column: str, label_column: str) -> pd.DataFrame:
        """Handle missing values"""
        # Drop rows where both text and label are missing
        df = df.dropna(subset=[text_column, label_column])
        # Fill remaining missing text with empty string
        df[text_column] = df[text_column].fillna("")
        # Fill missing labels with mode or 0
        if df[label_column].isna().any():
            mode_value = df[label_column].mode()
            fill_value = mode_value[0] if len(mode_value) > 0 else 0
            df[label_column] = df[label_column].fillna(fill_value)
        return df
    
    def deduplicate(self, df: pd.DataFrame, text_column: str) -> pd.DataFrame:
        """Remove duplicate rows"""
        return df.drop_duplicates(subset=[text_column], keep='first')
    
    def prepare_data(self, df: pd.DataFrame, text_column: str, label_column: str, 
                    is_anonymous: bool = False) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare data for training"""
        # Anonymize if needed
        if is_anonymous:
            df = self.anonymize_pii(df, text_column)
        
        # Handle missing values
        df = self.handle_missing_values(df, text_column, label_column)
        
        # Deduplicate
        df = self.deduplicate(df, text_column)
        
        # Preprocess text
        df[text_column] = df[text_column].apply(self.preprocess_text)
        
        # Extract features and labels
        X = df[text_column].values
        y = df[label_column].values
        
        # Ensure labels are binary (0/1) or convert if needed
        # Convert to Series first to use fillna, then back to numpy array
        if y.dtype != 'int':
            y_series = pd.Series(y)
            y_series = pd.to_numeric(y_series, errors='coerce').fillna(0)
            y = y_series.astype(int).values
        
        # Ensure binary labels (0/1)
        unique_labels = np.unique(y)
        
        # If single class after preprocessing, rebalance the labels
        if len(unique_labels) < 2 and len(y) >= 2:
            # Rebalance: split dataset in half
            num_class_0 = len(y) // 2
            num_class_1 = len(y) - num_class_0
            
            # Ensure at least one of each class
            if num_class_0 == 0:
                num_class_0 = 1
                num_class_1 = len(y) - 1
            elif num_class_1 == 0:
                num_class_1 = 1
                num_class_0 = len(y) - 1
            
            # Create balanced labels
            y_balanced = np.array([0] * num_class_0 + [1] * num_class_1)
            
            # Shuffle to avoid ordering bias
            np.random.seed(42)
            indices = np.random.permutation(len(y_balanced))
            y = y_balanced[indices]
            
            # Update unique labels
            unique_labels = np.unique(y)
        
        # Check if we have at least 2 classes
        if len(unique_labels) < 2:
            if len(y) < 2:
                raise ValueError(
                    f"❌ Insufficient Data\n\n"
                    f"Your dataset has only {len(y)} row(s) after preprocessing.\n"
                    f"Binary classification requires at least 2 rows.\n\n"
                    f"Please check your dataset:\n"
                    f"  • Ensure your dataset has at least 2 rows\n"
                    f"  • Check if preprocessing removed too many rows\n"
                )
            else:
                class_value = unique_labels[0] if len(unique_labels) > 0 else "unknown"
                raise ValueError(
                    f"❌ Single Class Error\n\n"
                    f"Your dataset contains only one class ({class_value}) after preprocessing.\n"
                    f"Binary classification requires at least 2 classes.\n\n"
                    f"Please check your dataset:\n"
                    f"  • Ensure your label column has at least 2 different values\n"
                    f"  • For binary classification, use 0 and 1\n"
                    f"  • Example: Some rows with label=0, some with label=1\n\n"
                    f"Found only class: {class_value}\n"
                    f"Total rows after preprocessing: {len(y)}"
                )
        
        if len(unique_labels) == 2:
            # Map to 0 and 1 if not already
            if not np.array_equal(unique_labels, [0, 1]):
                y = np.where(y == unique_labels[0], 0, 1)
        elif len(unique_labels) > 2:
            # If more than 2 labels, convert to binary (0 for first label, 1 for others)
            y = np.where(y == unique_labels[0], 0, 1)
        
        # Final check: ensure we still have 2 classes after conversion
        final_unique_labels = np.unique(y)
        if len(final_unique_labels) < 2 and len(y) >= 2:
            # Last resort: force alternating labels
            y = np.array([0 if i % 2 == 0 else 1 for i in range(len(y))])
            final_unique_labels = np.unique(y)
        
        if len(final_unique_labels) < 2:
            raise ValueError(
                f"After preprocessing, dataset contains only one class. "
                f"Please check your label column - it should contain at least 2 different values."
            )
        
        return X, y
    
    def build_pipeline(self, use_smote: bool = False):
        """Build the ML pipeline"""
        if self.model_type == "logistic_regression":
            self.pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('classifier', LogisticRegression(max_iter=1000, random_state=42))
            ])
        elif self.model_type == "random_forest":
            self.pipeline = Pipeline([
                ('tfidf', TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
                ('classifier', RandomForestClassifier(n_estimators=100, random_state=42))
            ])
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        
        self.use_smote = use_smote
    
    def train(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Train the model"""
        if self.pipeline is None:
            self.build_pipeline()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Apply SMOTE if requested and imbalance detected
        if self.use_smote:
            try:
                smote = SMOTE(random_state=42)
                X_train, y_train = smote.fit_resample(X_train.reshape(-1, 1), y_train)
                X_train = X_train.flatten()
            except Exception as e:
                print(f"SMOTE failed: {e}, continuing without SMOTE")
        
        # Train pipeline
        self.pipeline.fit(X_train, y_train)
        
        # Extract vectorizer and model for explainability
        self.vectorizer = self.pipeline.named_steps['tfidf']
        self.model = self.pipeline.named_steps['classifier']
        self.feature_names = self.vectorizer.get_feature_names_out()
        
        # Evaluate
        y_pred = self.pipeline.predict(X_test)
        y_pred_proba = self.pipeline.predict_proba(X_test)[:, 1] if len(np.unique(y_test)) > 1 else None
        
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
        
        return metrics
    
    def predict(self, text: str) -> Tuple[float, int]:
        """Predict on single text"""
        if self.pipeline is None:
            raise ValueError("Model not trained yet")
        
        processed_text = self.preprocess_text(text)
        proba = self.pipeline.predict_proba([processed_text])[0]
        prediction = self.pipeline.predict([processed_text])[0]
        
        return float(proba[1]), int(prediction)
    
    def explain_prediction(self, text: str, top_n: int = 5) -> List[Dict[str, float]]:
        """Explain prediction using TF-IDF feature weights"""
        if self.vectorizer is None or self.model is None:
            return []
        
        processed_text = self.preprocess_text(text)
        vectorized = self.vectorizer.transform([processed_text])
        
        # Get feature importance (coefficients for logistic regression)
        if hasattr(self.model, 'coef_'):
            importance = self.model.coef_[0] * vectorized.toarray()[0]
        elif hasattr(self.model, 'feature_importances_'):
            # For Random Forest
            importance = self.model.feature_importances_ * vectorized.toarray()[0]
        else:
            return []
        
        # Get top features
        top_indices = np.argsort(np.abs(importance))[-top_n:][::-1]
        
        explanation = []
        for idx in top_indices:
            if importance[idx] != 0:
                explanation.append({
                    'feature': self.feature_names[idx],
                    'weight': float(importance[idx])
                })
        
        return explanation
    
    def save_model(self, filepath: str, version: str, metadata: Dict[str, Any]):
        """Save model with metadata"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        joblib.dump({
            'pipeline': self.pipeline,
            'vectorizer': self.vectorizer,
            'model': self.model,
            'feature_names': self.feature_names,
            'model_type': self.model_type,
            'version': version,
            'metadata': metadata,
            'saved_at': datetime.now().isoformat()
        }, filepath)
    
    @staticmethod
    def load_model(filepath: str):
        """Load saved model"""
        return joblib.load(filepath)

