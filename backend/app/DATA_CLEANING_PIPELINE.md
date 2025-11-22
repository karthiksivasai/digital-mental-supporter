# Dataset Cleaning Pipeline Documentation

## Overview

The `DatasetCleaningPipeline` is an Auto-ML style automated data preprocessing pipeline that handles all common data cleaning tasks automatically. It's designed to be flexible, configurable, and production-ready.

## Features

✅ **Missing Value Handling** - Multiple strategies (auto, drop, mean, median, mode, KNN)  
✅ **Normalization** - Standard, Min-Max, or Robust scaling  
✅ **Outlier Removal** - IQR or Z-score methods  
✅ **Encoding** - Automatic categorical encoding (label, one-hot, ordinal)  
✅ **Train-Test Split** - Stratified splitting with configurable test size  
✅ **SMOTE** - Optional oversampling for imbalanced datasets  

## Quick Start

### Basic Usage

```python
from app.data_cleaning_pipeline import DatasetCleaningPipeline
import pandas as pd

# Load your dataset
df = pd.read_csv('your_dataset.csv')

# Initialize pipeline with default settings
pipeline = DatasetCleaningPipeline()

# Clean and split data
X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
    df, target_column='label'
)

# Use cleaned data for training
# X_train, X_test are numpy arrays ready for ML models
```

### Custom Configuration

```python
pipeline = DatasetCleaningPipeline(
    missing_value_strategy="auto",    # "auto", "drop", "mean", "median", "mode", "knn"
    normalization_method="standard",   # "standard", "minmax", "robust", "none"
    outlier_method="iqr",              # "iqr", "zscore", "none"
    outlier_threshold=1.5,             # Multiplier for IQR method
    encoding_method="auto",            # "auto", "label", "onehot", "ordinal"
    test_size=0.2,                     # Proportion for test set
    random_state=42,                   # Reproducibility seed
    use_smote=True,                    # Enable SMOTE for imbalanced data
    smote_k_neighbors=5                # Neighbors for SMOTE
)
```

## Detailed Feature Guide

### 1. Missing Value Handling

The pipeline automatically handles missing values based on your strategy:

- **`"auto"`** (default): Intelligently selects strategy based on data type and missing ratio
  - Drops columns with >50% missing values
  - Uses median for numeric columns
  - Uses mode for categorical/text columns

- **`"drop"`**: Removes rows with any missing values

- **`"mean"`**: Fills numeric columns with mean value

- **`"median"`**: Fills numeric columns with median value (robust to outliers)

- **`"mode"`**: Fills with most frequent value

- **`"knn"`**: Uses K-Nearest Neighbors imputation for numeric columns

```python
pipeline = DatasetCleaningPipeline(missing_value_strategy="median")
```

### 2. Normalization

Normalize numeric features to improve model performance:

- **`"standard"`** (default): StandardScaler (mean=0, std=1)
- **`"minmax"`**: MinMaxScaler (range 0-1)
- **`"robust"`**: RobustScaler (uses median/IQR, robust to outliers)
- **`"none"`**: No normalization

```python
pipeline = DatasetCleaningPipeline(normalization_method="minmax")
```

### 3. Outlier Removal

Detect and remove outliers from numeric columns:

- **`"iqr"`** (default): Interquartile Range method
  - Removes values outside [Q1 - threshold*IQR, Q3 + threshold*IQR]
  - Default threshold: 1.5

- **`"zscore"`**: Z-score method
  - Removes values with |z-score| > 3

- **`"none"`**: No outlier removal

```python
pipeline = DatasetCleaningPipeline(
    outlier_method="zscore",
    outlier_threshold=2.0  # For IQR method
)
```

### 4. Encoding

Automatically encode categorical variables:

- **`"auto"`** (default): 
  - One-hot encoding for low cardinality (<10 unique values)
  - Label encoding for high cardinality
  - Target column always label encoded

- **`"label"`**: Label encoding for all categorical columns

- **`"onehot"`**: One-hot encoding (except target column)

- **`"ordinal"`**: Ordinal encoding

```python
pipeline = DatasetCleaningPipeline(encoding_method="onehot")
```

### 5. Train-Test Split

Automatically splits data with stratification:

```python
pipeline = DatasetCleaningPipeline(test_size=0.3)  # 30% test set
```

### 6. SMOTE (Synthetic Minority Oversampling)

Handle imbalanced datasets:

```python
pipeline = DatasetCleaningPipeline(
    use_smote=True,
    smote_k_neighbors=5
)
```

SMOTE is only applied if:
- Dataset is imbalanced (ratio > 1.5)
- At least 2 classes exist
- Sufficient samples for k-neighbors

## Advanced Usage

### Step-by-Step Processing

Instead of using `clean_and_split()`, you can apply steps individually:

```python
pipeline = DatasetCleaningPipeline()

# Step 1: Handle missing values
df_cleaned, info = pipeline.fit_transform(df, target_column='label')

# Step 2: Extract features and target
X = df_cleaned.drop(columns=['label']).values
y = df_cleaned['label'].values

# Step 3: Split data
X_train, X_test, y_train, y_test = pipeline.split_data(X, y)

# Step 4: Apply SMOTE (optional)
X_train, y_train = pipeline.apply_smote(X_train, y_train)
```

### Inference on New Data

Use the `transform()` method to preprocess new data using fitted transformers:

```python
# After training
pipeline.fit_transform(df_train, target_column='label')

# For new predictions
new_data = pd.DataFrame({'feature1': [1, 2], 'feature2': [3, 4]})
new_data_cleaned = pipeline.transform(new_data)
```

### Getting Preprocessing Information

Access detailed preprocessing statistics:

```python
X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
    df, target_column='label'
)

print(info)
# {
#     'initial_shape': (1000, 5),
#     'final_shape': (950, 6),
#     'missing_values': {...},
#     'outliers': {...},
#     'encoding': {...},
#     'normalization': {...},
#     'smote': {...},
#     'train_test_split': {...}
# }
```

## Integration with Existing Code

### Integration with auto_trainer.py

You can integrate the cleaning pipeline with your existing training code:

```python
from app.data_cleaning_pipeline import DatasetCleaningPipeline
from app.auto_trainer import train_multiple_models

# Load dataset
df = pd.read_csv('dataset.csv')

# Clean data
pipeline = DatasetCleaningPipeline(
    use_smote=True,
    normalization_method="standard"
)
X_train, X_test, y_train, y_test, info = pipeline.clean_and_split(
    df, target_column='label'
)

# Train models
results = train_multiple_models(
    X_train, y_train, X_test, y_test,
    use_smote=False  # Already applied in pipeline
)
```

### Integration with MLPipeline

The cleaning pipeline complements the existing `MLPipeline` class:

```python
from app.data_cleaning_pipeline import DatasetCleaningPipeline
from app.ml_pipeline import MLPipeline

# Clean structured/numeric features
cleaning_pipeline = DatasetCleaningPipeline()
df_cleaned, _ = cleaning_pipeline.fit_transform(df, target_column='label')

# Use MLPipeline for text features
ml_pipeline = MLPipeline()
X_text, y = ml_pipeline.prepare_data(
    df_cleaned, text_column='text', label_column='label'
)
```

## Best Practices

1. **Always specify target_column**: The target column is never modified (except encoding if categorical)

2. **Use "auto" strategies**: The auto mode intelligently selects the best strategy based on your data

3. **Check preprocessing info**: Review the `info` dictionary to understand what transformations were applied

4. **Save transformers**: If you need to preprocess new data later, keep the pipeline instance with fitted transformers

5. **Handle text columns separately**: Text columns are preserved but not normalized. Use TF-IDF or other text vectorization separately

6. **SMOTE considerations**: 
   - Only use SMOTE on training data, not test data
   - Ensure sufficient samples for k-neighbors
   - Monitor for overfitting

## Example Use Cases

### 1. Structured Data Classification

```python
pipeline = DatasetCleaningPipeline(
    missing_value_strategy="auto",
    normalization_method="standard",
    outlier_method="iqr",
    encoding_method="auto",
    use_smote=True
)
```

### 2. Regression Tasks

```python
pipeline = DatasetCleaningPipeline(
    missing_value_strategy="median",
    normalization_method="robust",  # Robust to outliers
    outlier_method="zscore",
    encoding_method="onehot",
    use_smote=False  # Not for regression
)
```

### 3. High-Dimensional Data

```python
pipeline = DatasetCleaningPipeline(
    missing_value_strategy="knn",      # Better for high-dim
    normalization_method="standard",
    outlier_method="none",             # May be too aggressive
    encoding_method="label",           # Avoid one-hot explosion
    use_smote=False
)
```

## Troubleshooting

### Issue: "No numeric columns found"
- **Solution**: Ensure your dataset has numeric columns, or disable normalization/outlier removal

### Issue: "SMOTE failed"
- **Solution**: Check if you have sufficient samples for k-neighbors, or disable SMOTE

### Issue: "Stratification failed"
- **Solution**: Ensure target column has at least 2 classes, or the pipeline will split without stratification

### Issue: "Outliers removed too many rows"
- **Solution**: Increase `outlier_threshold` or use `outlier_method="none"`

## API Reference

See `data_cleaning_pipeline.py` for complete API documentation.

## Examples

Run the example script to see the pipeline in action:

```bash
cd backend
python -m app.data_cleaning_example
```

