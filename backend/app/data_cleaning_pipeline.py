"""
Auto-ML Style Dataset Cleaning Pipeline
Comprehensive automated data preprocessing pipeline
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Union
from sklearn.preprocessing import (
    StandardScaler, MinMaxScaler, RobustScaler,
    LabelEncoder, OneHotEncoder, OrdinalEncoder
)
from sklearn.model_selection import train_test_split
from sklearn.impute import SimpleImputer, KNNImputer
from imblearn.over_sampling import SMOTE
import warnings
warnings.filterwarnings('ignore')


class DatasetCleaningPipeline:
    """
    Automated dataset cleaning pipeline with Auto-ML style preprocessing
    
    Features:
    - Missing value handling (multiple strategies)
    - Normalization (multiple scalers)
    - Outlier removal (IQR, Z-score methods)
    - Encoding (label, one-hot, ordinal)
    - Train-test split
    - SMOTE (optional for imbalanced datasets)
    """
    
    def __init__(
        self,
        missing_value_strategy: str = "auto",  # "auto", "drop", "mean", "median", "mode", "knn"
        normalization_method: str = "standard",  # "standard", "minmax", "robust", "none"
        outlier_method: str = "iqr",  # "iqr", "zscore", "none"
        outlier_threshold: float = 1.5,  # For IQR method
        encoding_method: str = "auto",  # "auto", "label", "onehot", "ordinal"
        test_size: float = 0.2,
        random_state: int = 42,
        use_smote: bool = False,
        smote_k_neighbors: int = 5
    ):
        """
        Initialize the cleaning pipeline
        
        Args:
            missing_value_strategy: Strategy for handling missing values
            normalization_method: Method for feature normalization
            outlier_method: Method for outlier detection/removal
            outlier_threshold: Threshold multiplier for IQR method
            encoding_method: Method for encoding categorical variables
            test_size: Proportion of dataset for testing
            random_state: Random seed for reproducibility
            use_smote: Whether to apply SMOTE for imbalanced datasets
            smote_k_neighbors: Number of neighbors for SMOTE
        """
        self.missing_value_strategy = missing_value_strategy
        self.normalization_method = normalization_method
        self.outlier_method = outlier_method
        self.outlier_threshold = outlier_threshold
        self.encoding_method = encoding_method
        self.test_size = test_size
        self.random_state = random_state
        self.use_smote = use_smote
        self.smote_k_neighbors = smote_k_neighbors
        
        # Store transformers for later use
        self.scalers = {}
        self.encoders = {}
        self.imputers = {}
        self.feature_names = []
        self.preprocessing_info = {}
        
    def _detect_column_types(self, df: pd.DataFrame) -> Dict[str, List[str]]:
        """Detect numeric, categorical, and text columns"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Distinguish between text and categorical
        text_cols = []
        true_categorical_cols = []
        
        for col in categorical_cols:
            # If column has high cardinality (>50 unique values) or avg length > 20, treat as text
            unique_ratio = df[col].nunique() / len(df)
            avg_length = df[col].astype(str).str.len().mean()
            
            if unique_ratio > 0.5 or avg_length > 20:
                text_cols.append(col)
            else:
                true_categorical_cols.append(col)
        
        return {
            'numeric': numeric_cols,
            'categorical': true_categorical_cols,
            'text': text_cols
        }
    
    def handle_missing_values(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Handle missing values using specified strategy
        
        Args:
            df: Input dataframe
            target_column: Target/label column name (will not be imputed)
        
        Returns:
            Cleaned dataframe
        """
        df = df.copy()
        initial_missing = df.isnull().sum().sum()
        
        if initial_missing == 0:
            self.preprocessing_info['missing_values'] = {
                'initial_missing': 0,
                'strategy': 'none',
                'final_missing': 0
            }
            return df
        
        # Drop rows where target is missing (critical)
        if target_column and target_column in df.columns:
            initial_len = len(df)
            df = df.dropna(subset=[target_column])
            dropped = initial_len - len(df)
            if dropped > 0:
                self.preprocessing_info['target_missing_dropped'] = dropped
        
        # Determine strategy
        strategy = self.missing_value_strategy
        if strategy == "auto":
            # Auto-select based on data type and missing ratio
            for col in df.columns:
                if col == target_column:
                    continue
                    
                missing_ratio = df[col].isnull().sum() / len(df)
                
                if missing_ratio > 0.5:
                    # More than 50% missing - drop column
                    df = df.drop(columns=[col])
                elif df[col].dtype in ['int64', 'float64']:
                    # Numeric: use median for robustness
                    df[col] = df[col].fillna(df[col].median())
                else:
                    # Categorical/text: use mode
                    mode_value = df[col].mode()
                    if len(mode_value) > 0:
                        df[col] = df[col].fillna(mode_value[0])
                    else:
                        df[col] = df[col].fillna("")
        elif strategy == "drop":
            # Drop rows with any missing values
            df = df.dropna()
        elif strategy == "mean":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col != target_column:
                    df[col] = df[col].fillna(df[col].mean())
        elif strategy == "median":
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            for col in numeric_cols:
                if col != target_column:
                    df[col] = df[col].fillna(df[col].median())
        elif strategy == "mode":
            for col in df.columns:
                if col != target_column:
                    mode_value = df[col].mode()
                    if len(mode_value) > 0:
                        df[col] = df[col].fillna(mode_value[0])
                    else:
                        df[col] = df[col].fillna("")
        elif strategy == "knn":
            # KNN imputation for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if target_column in numeric_cols:
                numeric_cols.remove(target_column)
            
            if len(numeric_cols) > 0:
                try:
                    imputer = KNNImputer(n_neighbors=5)
                    df[numeric_cols] = imputer.fit_transform(df[numeric_cols])
                    self.imputers['knn'] = imputer
                except Exception as e:
                    # Fallback to median if KNN fails
                    for col in numeric_cols:
                        df[col] = df[col].fillna(df[col].median())
        
        final_missing = df.isnull().sum().sum()
        self.preprocessing_info['missing_values'] = {
            'initial_missing': int(initial_missing),
            'strategy': strategy,
            'final_missing': int(final_missing),
            'rows_dropped': int(initial_missing - final_missing)
        }
        
        return df
    
    def remove_outliers(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Remove outliers using specified method
        
        Args:
            df: Input dataframe
            target_column: Target column (will not be used for outlier detection)
        
        Returns:
            Dataframe with outliers removed
        """
        if self.outlier_method == "none":
            self.preprocessing_info['outliers'] = {
                'method': 'none',
                'outliers_removed': 0
            }
            return df
        
        df = df.copy()
        initial_len = len(df)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if target_column in numeric_cols:
            numeric_cols.remove(target_column)
        
        if len(numeric_cols) == 0:
            self.preprocessing_info['outliers'] = {
                'method': self.outlier_method,
                'outliers_removed': 0,
                'reason': 'no_numeric_columns'
            }
            return df
        
        outlier_mask = pd.Series([True] * len(df))
        
        if self.outlier_method == "iqr":
            # Interquartile Range method
            for col in numeric_cols:
                Q1 = df[col].quantile(0.25)
                Q3 = df[col].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - self.outlier_threshold * IQR
                upper_bound = Q3 + self.outlier_threshold * IQR
                
                col_mask = (df[col] >= lower_bound) & (df[col] <= upper_bound)
                outlier_mask = outlier_mask & col_mask
        
        elif self.outlier_method == "zscore":
            # Z-score method (threshold = 3)
            for col in numeric_cols:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                col_mask = z_scores < 3
                outlier_mask = outlier_mask & col_mask
        
        df = df[outlier_mask].reset_index(drop=True)
        outliers_removed = initial_len - len(df)
        
        self.preprocessing_info['outliers'] = {
            'method': self.outlier_method,
            'outliers_removed': int(outliers_removed),
            'columns_checked': numeric_cols
        }
        
        return df
    
    def encode_features(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Encode categorical features
        
        Args:
            df: Input dataframe
            target_column: Target column (will be label encoded if categorical)
        
        Returns:
            Dataframe with encoded features
        """
        df = df.copy()
        column_types = self._detect_column_types(df)
        categorical_cols = column_types['categorical']
        
        if len(categorical_cols) == 0:
            self.preprocessing_info['encoding'] = {
                'method': 'none',
                'columns_encoded': []
            }
            return df
        
        # Determine encoding method
        encoding_method = self.encoding_method
        if encoding_method == "auto":
            # Auto-select: one-hot for low cardinality (<10), label for high cardinality
            for col in categorical_cols:
                if col == target_column:
                    # Target: always label encode
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
                    self.encoders[col] = le
                else:
                    unique_count = df[col].nunique()
                    if unique_count < 10:
                        # One-hot encoding for low cardinality
                        dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                        df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
                        self.encoders[col] = 'onehot'
                    else:
                        # Label encoding for high cardinality
                        le = LabelEncoder()
                        df[col] = le.fit_transform(df[col].astype(str))
                        self.encoders[col] = le
        elif encoding_method == "label":
            # Label encoding for all categorical
            for col in categorical_cols:
                le = LabelEncoder()
                df[col] = le.fit_transform(df[col].astype(str))
                self.encoders[col] = le
        elif encoding_method == "onehot":
            # One-hot encoding for all categorical (except target)
            for col in categorical_cols:
                if col == target_column:
                    le = LabelEncoder()
                    df[col] = le.fit_transform(df[col].astype(str))
                    self.encoders[col] = le
                else:
                    dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
                    df = pd.concat([df.drop(columns=[col]), dummies], axis=1)
                    self.encoders[col] = 'onehot'
        elif encoding_method == "ordinal":
            # Ordinal encoding
            for col in categorical_cols:
                oe = OrdinalEncoder()
                df[col] = oe.fit_transform(df[[col]])
                self.encoders[col] = oe
        
        encoded_cols = list(self.encoders.keys())
        self.preprocessing_info['encoding'] = {
            'method': encoding_method,
            'columns_encoded': encoded_cols
        }
        
        return df
    
    def normalize_features(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None,
        fit: bool = True
    ) -> pd.DataFrame:
        """
        Normalize numeric features
        
        Args:
            df: Input dataframe
            target_column: Target column (will not be normalized)
            fit: Whether to fit scalers (True for training, False for inference)
        
        Returns:
            Dataframe with normalized features
        """
        if self.normalization_method == "none":
            self.preprocessing_info['normalization'] = {
                'method': 'none',
                'columns_normalized': []
            }
            return df
        
        df = df.copy()
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if target_column in numeric_cols:
            numeric_cols.remove(target_column)
        
        if len(numeric_cols) == 0:
            self.preprocessing_info['normalization'] = {
                'method': self.normalization_method,
                'columns_normalized': []
            }
            return df
        
        # Select scaler
        if self.normalization_method == "standard":
            scaler_class = StandardScaler
        elif self.normalization_method == "minmax":
            scaler_class = MinMaxScaler
        elif self.normalization_method == "robust":
            scaler_class = RobustScaler
        else:
            return df
        
        # Normalize each column
        for col in numeric_cols:
            if fit:
                scaler = scaler_class()
                df[col] = scaler.fit_transform(df[[col]]).flatten()
                self.scalers[col] = scaler
            else:
                if col in self.scalers:
                    df[col] = self.scalers[col].transform(df[[col]]).flatten()
                else:
                    # If scaler not fitted, fit it now (shouldn't happen in normal flow)
                    scaler = scaler_class()
                    df[col] = scaler.fit_transform(df[[col]]).flatten()
                    self.scalers[col] = scaler
        
        self.preprocessing_info['normalization'] = {
            'method': self.normalization_method,
            'columns_normalized': numeric_cols
        }
        
        return df
    
    def apply_smote(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply SMOTE for imbalanced datasets
        
        Args:
            X: Feature array
            y: Target array
        
        Returns:
            Resampled X and y
        """
        if not self.use_smote:
            return X, y
        
        try:
            # Check if dataset is imbalanced
            unique, counts = np.unique(y, return_counts=True)
            if len(unique) < 2:
                return X, y
            
            # Calculate imbalance ratio
            min_class_count = counts.min()
            max_class_count = counts.max()
            imbalance_ratio = max_class_count / min_class_count
            
            # Only apply SMOTE if imbalance ratio > 1.5
            if imbalance_ratio > 1.5:
                smote = SMOTE(
                    random_state=self.random_state,
                    k_neighbors=min(self.smote_k_neighbors, min_class_count - 1)
                )
                X_resampled, y_resampled = smote.fit_resample(X, y)
                
                self.preprocessing_info['smote'] = {
                    'applied': True,
                    'original_shape': X.shape,
                    'resampled_shape': X_resampled.shape,
                    'imbalance_ratio': float(imbalance_ratio)
                }
                return X_resampled, y_resampled
            else:
                self.preprocessing_info['smote'] = {
                    'applied': False,
                    'reason': 'dataset_balanced',
                    'imbalance_ratio': float(imbalance_ratio)
                }
                return X, y
        except Exception as e:
            self.preprocessing_info['smote'] = {
                'applied': False,
                'error': str(e)
            }
            return X, y
    
    def split_data(
        self,
        X: np.ndarray,
        y: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Split data into train and test sets
        
        Args:
            X: Feature array
            y: Target array
        
        Returns:
            X_train, X_test, y_train, y_test
        """
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=self.test_size,
                random_state=self.random_state,
                stratify=y if len(np.unique(y)) > 1 else None
            )
            
            self.preprocessing_info['train_test_split'] = {
                'test_size': self.test_size,
                'train_size': len(X_train),
                'test_size_actual': len(X_test),
                'stratify': len(np.unique(y)) > 1
            }
            
            return X_train, X_test, y_train, y_test
        except Exception as e:
            # If stratification fails, split without it
            X_train, X_test, y_train, y_test = train_test_split(
                X, y,
                test_size=self.test_size,
                random_state=self.random_state
            )
            
            self.preprocessing_info['train_test_split'] = {
                'test_size': self.test_size,
                'train_size': len(X_train),
                'test_size_actual': len(X_test),
                'stratify': False,
                'note': 'stratification_failed'
            }
            
            return X_train, X_test, y_train, y_test
    
    def fit_transform(
        self,
        df: pd.DataFrame,
        target_column: str
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Apply all preprocessing steps to training data
        
        Args:
            df: Input dataframe
            target_column: Name of target/label column
        
        Returns:
            Cleaned dataframe and preprocessing info
        """
        self.preprocessing_info = {
            'initial_shape': df.shape,
            'target_column': target_column
        }
        
        # Step 1: Handle missing values
        df = self.handle_missing_values(df, target_column)
        
        # Step 2: Remove outliers
        df = self.remove_outliers(df, target_column)
        
        # Step 3: Encode categorical features
        df = self.encode_features(df, target_column)
        
        # Step 4: Normalize features
        df = self.normalize_features(df, target_column, fit=True)
        
        self.preprocessing_info['final_shape'] = df.shape
        self.feature_names = [col for col in df.columns if col != target_column]
        
        return df, self.preprocessing_info
    
    def transform(
        self,
        df: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Apply preprocessing to new data (inference)
        
        Args:
            df: Input dataframe
            target_column: Optional target column name
        
        Returns:
            Transformed dataframe
        """
        # Apply same transformations but without fitting
        df = df.copy()
        
        # Handle missing values (using same strategy)
        df = self.handle_missing_values(df, target_column)
        
        # Note: Outlier removal typically not applied during inference
        # But we can apply it if needed
        
        # Encode features (using fitted encoders)
        if self.encoders:
            for col, encoder in self.encoders.items():
                if col in df.columns:
                    if isinstance(encoder, LabelEncoder):
                        # Handle unseen categories
                        unique_values = set(df[col].astype(str).unique())
                        known_classes = set(encoder.classes_)
                        unknown_values = unique_values - known_classes
                        
                        if unknown_values:
                            # Map unknown to most frequent class
                            df[col] = df[col].astype(str).replace(
                                list(unknown_values),
                                encoder.classes_[0]
                            )
                        df[col] = encoder.transform(df[col].astype(str))
                    elif isinstance(encoder, OrdinalEncoder):
                        df[col] = encoder.transform(df[[col]])
                    # One-hot encoding handled differently (would need to recreate)
        
        # Normalize features (using fitted scalers)
        df = self.normalize_features(df, target_column, fit=False)
        
        return df
    
    def clean_and_split(
        self,
        df: pd.DataFrame,
        target_column: str,
        return_dataframe: bool = False
    ) -> Union[
        Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]],
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, Dict[str, Any]]
    ]:
        """
        Complete pipeline: clean data and split into train/test
        
        Args:
            df: Input dataframe
            target_column: Name of target/label column
            return_dataframe: If True, return DataFrames; if False, return numpy arrays
        
        Returns:
            X_train, X_test, y_train, y_test, preprocessing_info
        """
        # Apply all preprocessing
        df_cleaned, preprocessing_info = self.fit_transform(df, target_column)
        
        # Extract features and target
        X = df_cleaned.drop(columns=[target_column]).values
        y = df_cleaned[target_column].values
        
        # Ensure y is numeric
        if y.dtype == 'object':
            le = LabelEncoder()
            y = le.fit_transform(y)
            if target_column not in self.encoders:
                self.encoders[target_column] = le
        
        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y)
        
        # Apply SMOTE to training data
        X_train, y_train = self.apply_smote(X_train, y_train)
        
        if return_dataframe:
            # Return as DataFrames
            feature_cols = [col for col in df_cleaned.columns if col != target_column]
            X_train_df = pd.DataFrame(X_train, columns=feature_cols)
            X_test_df = pd.DataFrame(X_test, columns=feature_cols)
            y_train_df = pd.DataFrame(y_train, columns=[target_column])
            y_test_df = pd.DataFrame(y_test, columns=[target_column])
            
            return X_train_df, X_test_df, y_train_df, y_test_df, preprocessing_info
        else:
            # Return as numpy arrays
            return X_train, X_test, y_train, y_test, preprocessing_info
    
    def get_preprocessing_info(self) -> Dict[str, Any]:
        """Get detailed preprocessing information"""
        return self.preprocessing_info
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names after preprocessing"""
        return self.feature_names.copy()

