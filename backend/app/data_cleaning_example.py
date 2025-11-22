"""
Example usage of the Dataset Cleaning Pipeline

This script demonstrates how to use the automated data cleaning pipeline
for preprocessing datasets before training ML models.
"""
import pandas as pd
import numpy as np
from app.data_cleaning_pipeline import DatasetCleaningPipeline


def example_basic_usage():
    """Basic usage example"""
    print("=" * 60)
    print("Example 1: Basic Usage")
    print("=" * 60)
    
    # Create sample dataset with various issues
    data = {
        'text': [
            'I feel sad and hopeless',
            'I am doing well',
            None,  # Missing value
            'I have trouble sleeping',
            'I feel great today',
            'I am doing well',  # Duplicate
            'Feeling anxious',
            'Happy and content'
        ],
        'age': [25, 30, None, 150, 28, 30, 22, 35],  # Outlier: 150
        'category': ['A', 'B', 'A', 'C', 'A', 'B', 'A', 'B'],
        'score': [0.5, 0.8, None, 0.3, 0.9, 0.8, 0.4, 0.7],
        'label': [0, 1, 0, 0, 1, 1, 0, 1]
    }
    
    df = pd.DataFrame(data)
    print("\nOriginal Dataset:")
    print(df)
    print(f"\nShape: {df.shape}")
    print(f"Missing values:\n{df.isnull().sum()}")
    
    # Initialize pipeline with default settings
    pipeline = DatasetCleaningPipeline(
        missing_value_strategy="auto",
        normalization_method="standard",
        outlier_method="iqr",
        encoding_method="auto",
        use_smote=False
    )
    
    # Clean and split data
    X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
        df, target_column='label'
    )
    
    print("\n" + "=" * 60)
    print("After Cleaning:")
    print("=" * 60)
    print(f"\nTraining set shape: {X_train.shape}")
    print(f"Test set shape: {X_test.shape}")
    print(f"\nPreprocessing Info:")
    print(f"  Initial shape: {info['initial_shape']}")
    print(f"  Final shape: {info['final_shape']}")
    print(f"  Missing values handled: {info.get('missing_values', {})}")
    print(f"  Outliers removed: {info.get('outliers', {})}")
    print(f"  Encoding applied: {info.get('encoding', {})}")
    print(f"  Normalization applied: {info.get('normalization', {})}")


def example_with_smote():
    """Example with SMOTE for imbalanced datasets"""
    print("\n" + "=" * 60)
    print("Example 2: Using SMOTE for Imbalanced Data")
    print("=" * 60)
    
    # Create imbalanced dataset
    np.random.seed(42)
    n_samples = 100
    data = {
        'feature1': np.random.randn(n_samples),
        'feature2': np.random.randn(n_samples),
        'feature3': np.random.randn(n_samples),
        'label': [0] * 80 + [1] * 20  # Imbalanced: 80% class 0, 20% class 1
    }
    
    df = pd.DataFrame(data)
    print(f"\nOriginal class distribution:")
    print(df['label'].value_counts())
    
    # Initialize pipeline with SMOTE enabled
    pipeline = DatasetCleaningPipeline(
        missing_value_strategy="auto",
        normalization_method="standard",
        outlier_method="zscore",
        encoding_method="auto",
        use_smote=True,  # Enable SMOTE
        smote_k_neighbors=5
    )
    
    # Clean and split
    X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
        df, target_column='label'
    )
    
    print(f"\nAfter SMOTE - Training set class distribution:")
    unique, counts = np.unique(y_train, return_counts=True)
    for u, c in zip(unique, counts):
        print(f"  Class {u}: {c} samples")
    
    print(f"\nSMOTE Info:")
    smote_info = info.get('smote', {})
    print(f"  Applied: {smote_info.get('applied', False)}")
    if smote_info.get('applied'):
        print(f"  Original shape: {smote_info.get('original_shape')}")
        print(f"  Resampled shape: {smote_info.get('resampled_shape')}")
        print(f"  Imbalance ratio: {smote_info.get('imbalance_ratio', 0):.2f}")


def example_custom_strategies():
    """Example with custom preprocessing strategies"""
    print("\n" + "=" * 60)
    print("Example 3: Custom Preprocessing Strategies")
    print("=" * 60)
    
    # Create dataset with categorical features
    data = {
        'numeric1': [1, 2, 3, 4, 5, 6, 7, 8],
        'numeric2': [10, 20, 30, 40, 50, 60, 70, 80],
        'category': ['low', 'medium', 'high', 'low', 'medium', 'high', 'low', 'medium'],
        'label': [0, 1, 0, 1, 0, 1, 0, 1]
    }
    
    df = pd.DataFrame(data)
    print("\nOriginal Dataset:")
    print(df)
    
    # Custom pipeline configuration
    pipeline = DatasetCleaningPipeline(
        missing_value_strategy="median",  # Use median for missing values
        normalization_method="minmax",    # Min-Max scaling
        outlier_method="iqr",             # IQR method
        outlier_threshold=2.0,            # Stricter outlier detection
        encoding_method="onehot",         # One-hot encoding for categories
        test_size=0.3,                    # 30% test set
        random_state=42,
        use_smote=False
    )
    
    X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
        df, target_column='label', return_dataframe=True
    )
    
    print("\nCleaned Training Features:")
    print(X_train.head())
    print(f"\nFeature names: {pipeline.get_feature_names()}")


def example_text_data():
    """Example for text classification datasets"""
    print("\n" + "=" * 60)
    print("Example 4: Text Classification Dataset")
    print("=" * 60)
    
    # Simulate text classification dataset
    data = {
        'text': [
            'I feel sad and hopeless',
            'I am doing well today',
            'Feeling anxious about work',
            'Happy and content',
            'Struggling with sleep',
            'Feeling great',
            'Very stressed',
            'Peaceful and calm'
        ],
        'sentiment_score': [0.2, 0.8, 0.3, 0.9, 0.4, 0.85, 0.25, 0.75],
        'word_count': [5, 5, 4, 3, 3, 2, 2, 3],
        'label': [0, 1, 0, 1, 0, 1, 0, 1]
    }
    
    df = pd.DataFrame(data)
    print("\nOriginal Dataset:")
    print(df)
    
    # Pipeline for text data (text columns are preserved)
    pipeline = DatasetCleaningPipeline(
        missing_value_strategy="auto",
        normalization_method="standard",
        outlier_method="iqr",
        encoding_method="auto",
        use_smote=False
    )
    
    X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
        df, target_column='label', return_dataframe=True
    )
    
    print("\nCleaned Features:")
    print(X_train.head())
    print(f"\nPreprocessing Summary:")
    for key, value in info.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")


if __name__ == "__main__":
    # Run all examples
    try:
        example_basic_usage()
        example_with_smote()
        example_custom_strategies()
        example_text_data()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

