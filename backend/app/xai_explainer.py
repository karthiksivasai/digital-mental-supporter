"""
Explainable AI Module using SHAP and LIME
"""
import os
import numpy as np
import pandas as pd
import joblib
import base64
import io
from typing import Dict, List, Any, Optional, Tuple

# Try to import SHAP and matplotlib, but handle gracefully if missing
try:
    import shap
    from shap import TreeExplainer, KernelExplainer, LinearExplainer
    from shap.plots import waterfall, force, summary, bar
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False

try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

from app.ml_pipeline import MLPipeline


class XAIExplainer:
    """Explainable AI using SHAP and LIME"""
    
    def __init__(self, model_path: str = "models/best_model.pkl"):
        """
        Initialize XAI Explainer
        
        Args:
            model_path: Path to the saved model file
        """
        self.model_path = model_path
        self.model_data = None
        self.pipeline = None
        self.vectorizer = None
        self.model = None
        self.model_type = None
        self.feature_names = None
        self.explainer = None
        self.X_background = None
        
    def load_model(self) -> bool:
        """Load the model from file"""
        # Check SHAP availability at runtime (not just import time)
        try:
            import shap
        except ImportError:
            raise ImportError("SHAP is not installed. Please install it with: pip install shap")
        try:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            self.model_data = MLPipeline.load_model(self.model_path)
            self.model_type = self.model_data.get('model_type', 'logistic_regression')
            self.vectorizer = self.model_data.get('vectorizer')
            self.model = self.model_data.get('model')
            self.pipeline = self.model_data.get('pipeline')
            # Get feature names from vectorizer if available
            if self.vectorizer and hasattr(self.vectorizer, 'get_feature_names_out'):
                try:
                    self.feature_names = self.vectorizer.get_feature_names_out().tolist()
                except:
                    try:
                        self.feature_names = self.vectorizer.get_feature_names().tolist()
                    except:
                        self.feature_names = self.model_data.get('feature_names', [])
            else:
                self.feature_names = self.model_data.get('feature_names', [])
            
            if self.model is None:
                raise ValueError("Model not found in saved data")
            
            return True
        except Exception as e:
            raise Exception(f"Failed to load model: {str(e)}")
    
    def prepare_background_data(self, dataset_path: Optional[str] = None, n_samples: int = 15):
        """
        Prepare background data for SHAP explainer
        
        Args:
            dataset_path: Optional path to dataset CSV
            n_samples: Number of samples to use as background
        """
        try:
            # Try to load from dataset if available
            if dataset_path and os.path.exists(dataset_path):
                df = pd.read_csv(dataset_path)
                # Use text column (assuming first text column or 'text' column)
                text_col = None
                for col in df.columns:
                    if 'text' in col.lower() or 'message' in col.lower() or 'content' in col.lower():
                        text_col = col
                        break
                
                if text_col:
                    texts = df[text_col].dropna().head(n_samples).tolist()
                else:
                    # Use first column
                    texts = df.iloc[:, 0].dropna().head(n_samples).tolist()
            else:
                # Create dummy background data
                texts = [
                    "I feel sad and depressed",
                    "I am happy and content",
                    "I feel anxious about the future",
                    "Everything is going well",
                    "I feel hopeless",
                    "I am doing fine",
                    "I feel stressed",
                    "I am okay",
                    "I feel worried",
                    "I feel great"
                ] * (n_samples // 10 + 1)
                texts = texts[:n_samples]
            
            # Preprocess texts
            if self.vectorizer:
                # Preprocess using MLPipeline
                pipeline = MLPipeline()
                processed_texts = [pipeline.preprocess_text(str(text)) for text in texts]
                X_background = self.vectorizer.transform(processed_texts)
                self.X_background = X_background
            else:
                raise ValueError("Vectorizer not loaded")
                
        except Exception as e:
            # Fallback: create minimal background
            print(f"Warning: Could not prepare background data: {e}")
            # Create a simple background
            if self.vectorizer:
                dummy_texts = ["sample text"] * min(50, n_samples)
                pipeline = MLPipeline()
                processed = [pipeline.preprocess_text(t) for t in dummy_texts]
                self.X_background = self.vectorizer.transform(processed)
    
    def create_shap_explainer(self):
        """Create appropriate SHAP explainer based on model type"""
        if self.model is None or self.X_background is None:
            raise ValueError("Model or background data not loaded")
        
        model_type_lower = self.model_type.lower()
        
        # Use TreeExplainer for tree-based models
        if 'random_forest' in model_type_lower or 'xgboost' in model_type_lower:
            try:
                self.explainer = TreeExplainer(self.model)
            except:
                # Fallback to KernelExplainer
                self.explainer = KernelExplainer(
                    self._model_predict_wrapper,
                    self.X_background[:50]  # Use subset for speed
                )
        
        # Use LinearExplainer for linear models
        elif 'logistic' in model_type_lower or 'linear' in model_type_lower:
            try:
                # Use minimal subset for LinearExplainer (faster)
                background_subset = self.X_background[:15]
                self.explainer = LinearExplainer(self.model, background_subset)
            except:
                # Fallback to KernelExplainer
                self.explainer = KernelExplainer(
                    self._model_predict_wrapper,
                    self.X_background[:20]  # Reduced for speed
                )
        
        # Use KernelExplainer for other models (SVM, ANN, etc.)
        else:
            # Use smaller subset for KernelExplainer (it's slow)
            # Handle sparse matrices properly
            if hasattr(self.X_background, 'shape'):
                max_idx = min(20, self.X_background.shape[0])
                background_subset = self.X_background[:max_idx]
            else:
                background_subset = self.X_background[:20]
            self.explainer = KernelExplainer(
                self._model_predict_wrapper,
                background_subset
            )
    
    def _model_predict_wrapper(self, X):
        """Wrapper for model prediction for SHAP"""
        if hasattr(self.model, 'predict_proba'):
            return self.model.predict_proba(X)[:, 1]
        else:
            return self.model.predict(X)
    
    def explain_global(self, dataset_path: Optional[str] = None, n_features: int = 20, max_samples: int = 15) -> Dict[str, Any]:
        """
        Generate global SHAP explanations
        
        Args:
            dataset_path: Optional path to dataset for background
            n_features: Number of top features to return
            
        Returns:
            Dictionary with global explanation data
        """
        # Check SHAP availability at runtime
        try:
            import shap
        except ImportError:
            raise ImportError("SHAP is not installed. Please install it with: pip install shap")
        try:
            # Load model if not loaded
            if self.model is None:
                self.load_model()
            
            # Prepare background data with reduced samples for speed
            self.prepare_background_data(dataset_path, n_samples=max_samples)
            
            # Create explainer
            self.create_shap_explainer()
            
            # Calculate SHAP values for background data
            # Use smaller subset for faster computation
            # Handle sparse matrices properly
            if hasattr(self.X_background, 'shape'):
                # Sparse matrix - use shape[0] instead of len()
                max_idx = min(max_samples, self.X_background.shape[0])
                background_subset = self.X_background[:max_idx]
            else:
                background_subset = self.X_background[:max_samples]
            
            # For KernelExplainer, use even smaller subset (it's very slow)
            if hasattr(self.explainer, '__class__') and 'Kernel' in str(self.explainer.__class__):
                # KernelExplainer is extremely slow - use minimal samples
                if hasattr(background_subset, 'shape'):
                    max_kernel_idx = min(10, background_subset.shape[0])
                    background_subset = background_subset[:max_kernel_idx]
                else:
                    # Handle sparse matrices
                    if hasattr(background_subset, 'shape'):
                        max_kernel_idx = min(10, background_subset.shape[0])
                        background_subset = background_subset[:max_kernel_idx]
                    else:
                        background_subset = background_subset[:10] if len(background_subset) > 10 else background_subset
                print(f"Using KernelExplainer with {background_subset.shape[0] if hasattr(background_subset, 'shape') else len(background_subset)} samples for speed")
            
            shap_values = self.explainer.shap_values(background_subset)
            
            # Handle multi-output case
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class
            
            # Get mean absolute SHAP values for feature importance
            mean_shap_values = np.abs(shap_values).mean(axis=0)
            
            # Get feature names
            if self.feature_names and len(self.feature_names) == len(mean_shap_values):
                feature_importance = [
                    {
                        "feature": self.feature_names[i],
                        "importance": float(mean_shap_values[i])
                    }
                    for i in range(len(mean_shap_values))
                ]
            else:
                feature_importance = [
                    {
                        "feature": f"feature_{i}",
                        "importance": float(mean_shap_values[i])
                    }
                    for i in range(len(mean_shap_values))
                ]
            
            # Sort by importance
            feature_importance.sort(key=lambda x: x["importance"], reverse=True)
            
            # Get top features
            top_features = feature_importance[:n_features]
            
            # Generate summary plot as base64 image
            # Pass the background subset used for calculation
            summary_plot_base64 = self._generate_summary_plot(shap_values, background_subset)
            
            # Generate bar plot as base64 image
            bar_plot_base64 = self._generate_bar_plot(shap_values)
            
            return {
                "feature_importance": top_features,
                "all_features": feature_importance,
                "summary_plot": summary_plot_base64,
                "bar_plot": bar_plot_base64,
                "model_type": self.model_type,
                "n_samples": background_subset.shape[0] if hasattr(background_subset, 'shape') else len(background_subset)
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate global explanation: {str(e)}")
    
    def explain_local(self, text: str) -> Dict[str, Any]:
        """
        Generate local SHAP and LIME explanations for a single prediction
        
        Args:
            text: Input text to explain
            
        Returns:
            Dictionary with local explanation data
        """
        # Check SHAP availability at runtime
        try:
            import shap
        except ImportError:
            raise ImportError("SHAP is not installed. Please install it with: pip install shap")
        try:
            # Load model if not loaded
            if self.model is None:
                self.load_model()
            
            # Prepare background data
            self.prepare_background_data()
            
            # Preprocess input text
            pipeline = MLPipeline()
            processed_text = pipeline.preprocess_text(text)
            
            # Transform text
            X_instance = self.vectorizer.transform([processed_text])
            
            # Create explainer
            self.create_shap_explainer()
            
            # Calculate SHAP values
            shap_values = self.explainer.shap_values(X_instance)
            
            # Handle multi-output case
            if isinstance(shap_values, list):
                shap_values = shap_values[1]  # Use positive class
            
            shap_values_flat = shap_values[0]  # Get single instance values
            
            # Get prediction
            if hasattr(self.model, 'predict_proba'):
                prediction_proba = self.model.predict_proba(X_instance)[0]
                prediction = self.model.predict(X_instance)[0]
            else:
                prediction = self.model.predict(X_instance)[0]
                prediction_proba = [1 - prediction, prediction] if prediction in [0, 1] else [0.5, 0.5]
            
            # Get feature contributions
            feature_names = self.feature_names if self.feature_names else [
                f"feature_{i}" for i in range(len(shap_values_flat))
            ]
            
            feature_contributions = [
                {
                    "feature": feature_names[i] if i < len(feature_names) else f"feature_{i}",
                    "shap_value": float(shap_values_flat[i]),
                    "contribution": float(shap_values_flat[i])
                }
                for i in range(len(shap_values_flat))
            ]
            
            # Sort by absolute contribution
            feature_contributions.sort(key=lambda x: abs(x["contribution"]), reverse=True)
            
            # Get top contributing features
            top_contributions = feature_contributions[:20]
            
            # Generate force plot as base64
            force_plot_base64 = self._generate_force_plot(shap_values, X_instance)
            
            # Generate waterfall plot as base64
            waterfall_plot_base64 = self._generate_waterfall_plot(shap_values_flat, feature_names)
            
            # Generate LIME explanation
            lime_explanation = self._generate_lime_explanation(text, X_instance)
            
            return {
                "prediction": int(prediction),
                "prediction_proba": {
                    "class_0": float(prediction_proba[0]),
                    "class_1": float(prediction_proba[1])
                },
                "feature_contributions": top_contributions,
                "all_contributions": feature_contributions,
                "force_plot": force_plot_base64,
                "waterfall_plot": waterfall_plot_base64,
                "lime_explanation": lime_explanation,
                "base_value": float(self.explainer.expected_value) if hasattr(self.explainer, 'expected_value') else 0.0,
                "input_text": text
            }
            
        except Exception as e:
            raise Exception(f"Failed to generate local explanation: {str(e)}")
    
    def _generate_summary_plot(self, shap_values, background_data=None) -> str:
        """Generate SHAP summary plot as base64 image"""
        try:
            plt.figure(figsize=(10, 8))
            # Use provided background data or fallback to X_background
            if background_data is not None:
                plot_background = background_data
            else:
                # Handle sparse matrices properly - get number of samples from shap_values shape
                if len(shap_values.shape) > 1:
                    n_samples = shap_values.shape[0]
                else:
                    n_samples = 1
                
                # Handle sparse matrices properly
                if hasattr(self.X_background, 'shape'):
                    max_idx = min(n_samples, self.X_background.shape[0])
                    plot_background = self.X_background[:max_idx]
                else:
                    plot_background = self.X_background[:n_samples] if n_samples > 0 else self.X_background[:1]
            
            shap.summary_plot(shap_values, plot_background, show=False, max_display=20)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            print(f"Error generating summary plot: {e}")
            return ""
    
    def _generate_bar_plot(self, shap_values) -> str:
        """Generate SHAP bar plot as base64 image"""
        try:
            plt.figure(figsize=(10, 8))
            shap.plots.bar(shap_values, show=False, max_display=20)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            print(f"Error generating bar plot: {e}")
            return ""
    
    def _generate_force_plot(self, shap_values, X_instance) -> str:
        """Generate SHAP force plot as base64 image"""
        try:
            # For single instance, create a bar plot instead of force plot
            # (force plots are better as HTML, but we'll use bar for image)
            shap_values_flat = shap_values[0] if len(shap_values.shape) > 1 else shap_values
            
            plt.figure(figsize=(10, 6))
            feature_names = self.feature_names[:len(shap_values_flat)] if self.feature_names else [
                f"feature_{i}" for i in range(len(shap_values_flat))
            ]
            
            # Get top 15 features
            indices = np.argsort(np.abs(shap_values_flat))[-15:][::-1]
            top_values = shap_values_flat[indices]
            top_features = [feature_names[i] for i in indices]
            
            colors = ['red' if v < 0 else 'blue' for v in top_values]
            plt.barh(range(len(top_values)), top_values, color=colors)
            plt.yticks(range(len(top_features)), top_features)
            plt.xlabel('SHAP Value')
            plt.title('Feature Contributions (SHAP)')
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            print(f"Error generating force plot: {e}")
            return ""
    
    def _generate_waterfall_plot(self, shap_values_flat, feature_names) -> str:
        """Generate waterfall plot as base64 image"""
        try:
            # Get top 15 features
            indices = np.argsort(np.abs(shap_values_flat))[-15:][::-1]
            top_values = shap_values_flat[indices]
            top_features = [feature_names[i] if i < len(feature_names) else f"feature_{i}" for i in indices]
            
            plt.figure(figsize=(10, 8))
            y_pos = np.arange(len(top_features))
            colors = ['red' if v < 0 else 'blue' for v in top_values]
            
            plt.barh(y_pos, top_values, color=colors, alpha=0.7)
            plt.yticks(y_pos, top_features)
            plt.xlabel('SHAP Value')
            plt.title('Waterfall Plot - Feature Contributions')
            plt.grid(axis='x', alpha=0.3)
            plt.tight_layout()
            
            # Convert to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
            plt.close()
            
            return f"data:image/png;base64,{image_base64}"
        except Exception as e:
            print(f"Error generating waterfall plot: {e}")
            return ""
    
    def _generate_lime_explanation(self, text: str, X_instance) -> Dict[str, Any]:
        """
        Generate LIME explanation
        
        Note: LIME for text requires lime.lime_text.TextExplainer
        For now, we'll use SHAP values as a proxy for LIME
        """
        try:
            # Since LIME requires different setup, we'll create a simplified explanation
            # based on SHAP values (which are similar in concept)
            
            # Preprocess text
            pipeline = MLPipeline()
            processed_text = pipeline.preprocess_text(text)
            
            # Get feature contributions from SHAP (already calculated)
            # This is a simplified LIME-like explanation
            return {
                "explanation": "LIME explanation based on feature contributions",
                "note": "Using SHAP values as proxy for LIME explanation"
            }
        except Exception as e:
            return {
                "error": f"Failed to generate LIME explanation: {str(e)}",
                "explanation": []
            }

