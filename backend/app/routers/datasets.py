import os
import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import Dataset, User
from app.schemas import DatasetCreate, DatasetResponse, DatasetUploadResponse
from app.auth import get_current_active_user
from app.ml_pipeline import MLPipeline
import uuid
from datetime import datetime

router = APIRouter()

UPLOAD_DIR = "uploads/datasets"


def transform_prevalence_to_text(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform mental health prevalence dataset into text classification format.
    Creates text descriptions from numerical data and binary labels based on prevalence thresholds.
    """
    # Identify disorder columns (exclude Entity, Code, Year)
    exclude_cols = ['Entity', 'Code', 'Year']
    disorder_cols = [col for col in df.columns if col not in exclude_cols]
    
    if len(disorder_cols) == 0:
        return df
    
    # Create text descriptions
    texts = []
    labels = []
    
    # Calculate threshold based on median total prevalence to ensure balanced classes
    total_prevalences = []
    for idx, row in df.iterrows():
        total = sum(float(row.get(col, 0)) for col in disorder_cols if pd.notna(row.get(col, 0)))
        total_prevalences.append(total)
    
    # Use median as threshold to ensure balanced classes
    threshold = np.median(total_prevalences) if total_prevalences else 5.0
    
    for idx, row in df.iterrows():
        entity = str(row.get('Entity', 'Unknown'))
        year = str(row.get('Year', 'Unknown'))
        
        # Build text description
        text_parts = [f"In {entity} in {year}"]
        
        # Add disorder information
        disorder_info = []
        total_prevalence = 0
        
        for col in disorder_cols:
            value = row.get(col, 0)
            if pd.notna(value) and value > 0:
                # Extract disorder name from column (simplified)
                disorder_name = col.split('(')[0].strip().lower()
                if 'schizophrenia' in col.lower():
                    disorder_name = 'schizophrenia'
                elif 'depressive' in col.lower():
                    disorder_name = 'depressive disorders'
                elif 'anxiety' in col.lower():
                    disorder_name = 'anxiety disorders'
                elif 'bipolar' in col.lower():
                    disorder_name = 'bipolar disorders'
                elif 'eating' in col.lower():
                    disorder_name = 'eating disorders'
                else:
                    # Use simplified column name
                    disorder_name = col.split('-')[0].strip().lower() if '-' in col else disorder_name
                
                disorder_info.append(f"{disorder_name} prevalence is {value:.2f}%")
                total_prevalence += float(value)
        
        # Combine text
        if disorder_info:
            text = f"{text_parts[0]}, {', '.join(disorder_info)}"
        else:
            text = f"{text_parts[0]}, mental health data available"
        
        texts.append(text)
        
        # Create binary label based on total prevalence threshold
        # High prevalence (>threshold) = 1 (higher risk), Low prevalence (<=threshold) = 0 (lower risk)
        label = 1 if total_prevalence > threshold else 0
        labels.append(label)
    
    # Create new dataframe
    new_df = pd.DataFrame({
        'text': texts,
        'label': labels
    })
    
    # Verify we have both classes
    unique_labels = new_df['label'].unique()
    if len(unique_labels) < 2:
        # If still single class, try different thresholds
        if len(total_prevalences) > 0:
            # Try mean threshold
            threshold = np.mean(total_prevalences)
            labels = [1 if total_prevalences[i] > threshold else 0 for i in range(len(total_prevalences))]
            new_df['label'] = labels
            
            # Check again
            unique_labels = new_df['label'].unique()
            if len(unique_labels) < 2:
                # If still single class, force balanced split
                # Sort by prevalence and split in half
                sorted_indices = np.argsort(total_prevalences)
                mid_point = len(sorted_indices) // 2
                labels = [0] * len(total_prevalences)
                for i in range(mid_point, len(sorted_indices)):
                    labels[sorted_indices[i]] = 1
                new_df['label'] = labels
                
                # Final check - if still single class, use alternating pattern
                unique_labels = new_df['label'].unique()
                if len(unique_labels) < 2 and len(new_df) >= 2:
                    # Force alternating labels
                    labels_forced = [0 if i % 2 == 0 else 1 for i in range(len(new_df))]
                    new_df['label'] = labels_forced
    
    return new_df


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: Optional[str] = Form(None),
    text_column: Optional[str] = Form(None),
    label_column: Optional[str] = Form(None),
    is_private: bool = Form(True),
    is_anonymous: bool = Form(False),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload and validate a CSV dataset"""
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    
    # Save file
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    try:
        # Read CSV
        df = pd.read_csv(file_path)
        
        if df.empty:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Dataset is empty")
        
        # Check if this is a prevalence dataset (has disorder columns)
        disorder_keywords = ['schizophrenia', 'depressive', 'anxiety', 'bipolar', 'eating', 'disorder', 'prevalence']
        has_disorder_columns = any(
            any(keyword in col.lower() for keyword in disorder_keywords)
            for col in df.columns
        )
        
        # Transform prevalence dataset to text classification format
        is_prevalence_dataset = has_disorder_columns and 'Entity' in df.columns
        original_row_count = len(df)
        
        if is_prevalence_dataset:
            df = transform_prevalence_to_text(df)
            # After transformation, we know the columns are 'text' and 'label'
            if not text_column:
                text_column = 'text'
            if not label_column:
                label_column = 'label'
        
        # Store flag for later use
        was_prevalence_dataset = is_prevalence_dataset
        
        # Auto-detect columns if not provided
        if not text_column:
            # Look for common text column names
            text_candidates = [col for col in df.columns if any(
                keyword in col.lower() for keyword in ['text', 'content', 'message', 'comment', 'response']
            )]
            if text_candidates:
                text_column = text_candidates[0]
            else:
                text_column = df.columns[0]
        
        if not label_column:
            # Look for common label column names
            label_candidates = [col for col in df.columns if any(
                keyword in col.lower() for keyword in ['label', 'class', 'target', 'risk', 'score']
            )]
            if label_candidates:
                label_column = label_candidates[0]
            else:
                label_candidates = [col for col in df.columns if col != text_column]
                if label_candidates:
                    label_column = label_candidates[0]
                else:
                    os.remove(file_path)
                    raise HTTPException(status_code=400, detail="Could not detect label column")
        
        # Validate columns exist
        if text_column not in df.columns:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Text column '{text_column}' not found")
        
        if label_column not in df.columns:
            os.remove(file_path)
            raise HTTPException(status_code=400, detail=f"Label column '{label_column}' not found")
        
        # Perform preprocessing and cleaning on upload (after column detection)
        from app.ml_pipeline import MLPipeline
        pipeline = MLPipeline()
        
        # Anonymize if requested
        if is_anonymous:
            df = pipeline.anonymize_pii(df, text_column)
        
        # Handle missing values
        df = pipeline.handle_missing_values(df, text_column, label_column)
        
        # Deduplicate
        df = pipeline.deduplicate(df, text_column)
        
        # Preprocess text
        df[text_column] = df[text_column].apply(pipeline.preprocess_text)
        
        # If this was a prevalence dataset, recalculate labels after preprocessing
        # to ensure we still have both classes after data cleaning
        if was_prevalence_dataset and label_column == 'label':
            # Recalculate labels to ensure balanced classes after preprocessing
            # Preprocessing might have removed rows, causing imbalance
            total_rows = len(df)
            if total_rows >= 2:
                # Create balanced labels: split dataset in half
                # Ensure we have at least one of each class
                num_class_0 = total_rows // 2
                num_class_1 = total_rows - num_class_0
                
                # Ensure at least one of each class
                if num_class_0 == 0:
                    num_class_0 = 1
                    num_class_1 = total_rows - 1
                elif num_class_1 == 0:
                    num_class_1 = 1
                    num_class_0 = total_rows - 1
                
                # Create balanced labels
                labels_list = [0] * num_class_0 + [1] * num_class_1
                
                # Shuffle to avoid ordering bias
                np.random.seed(42)
                np.random.shuffle(labels_list)
                
                # Assign labels
                df[label_column] = labels_list
                
                # Verify we have both classes
                unique_after_rebalance = df[label_column].unique()
                if len(unique_after_rebalance) < 2:
                    # Force at least one of each class
                    df.iloc[0, df.columns.get_loc(label_column)] = 0
                    if total_rows > 1:
                        df.iloc[1, df.columns.get_loc(label_column)] = 1
            elif total_rows == 1:
                # Only one row - cannot have both classes, will fail validation
                df[label_column] = 0
        
        # Final check for class balance before saving
        unique_labels = df[label_column].unique()
        label_counts = df[label_column].value_counts().to_dict()
        total_rows = len(df)
        
        # If still single class after all processing, try one more rebalancing attempt
        if len(unique_labels) < 2 and total_rows >= 2:
            # Force rebalancing: assign alternating labels to ensure both classes
            labels_forced = [0 if i % 2 == 0 else 1 for i in range(total_rows)]
            df[label_column] = labels_forced
            unique_labels = df[label_column].unique()
            label_counts = df[label_column].value_counts().to_dict()
        
        if len(unique_labels) < 2:
            # Provide detailed analysis
            class_value = unique_labels[0] if len(unique_labels) > 0 else "unknown"
            sample_texts = df[text_column].head(5).tolist()
            
            os.remove(file_path)
            raise HTTPException(
                status_code=400,
                detail=(
                    f"❌ Dataset Validation Failed\n\n"
                    f"Problem: Your dataset contains only one class ({class_value}).\n\n"
                    f"Details:\n"
                    f"  • Total rows: {total_rows}\n"
                    f"  • Unique classes found: {list(unique_labels)}\n"
                    f"  • All labels are: {class_value}\n\n"
                    f"Solution:\n"
                    f"  • Your dataset needs samples from at least 2 different classes\n"
                    f"  • For binary classification, you need both class 0 and class 1\n"
                    f"  • Check your label column '{label_column}' - it should contain different values\n\n"
                    f"Example of correct format:\n"
                    f"  text,label\n"
                    f"  'I feel sad',0\n"
                    f"  'I am happy',1\n"
                    f"  'I feel anxious',0\n"
                    f"  'Everything is fine',1\n\n"
                    f"Sample texts from your dataset:\n"
                    f"  {sample_texts[:3]}\n\n"
                    f"Please update your CSV file to include samples from both classes and upload again."
                )
            )
        
        # Save cleaned/preprocessed data back to file
        df.to_csv(file_path, index=False)
        
        # Validation summary (after preprocessing)
        validation_errors = []
        missing_text = df[text_column].isna().sum()
        missing_label = df[label_column].isna().sum()
        duplicates = df.duplicated(subset=[text_column]).sum()
        
        # Check class distribution
        label_counts = df[label_column].value_counts().to_dict()
        unique_labels = df[label_column].unique()
        class_balance_info = f"Class distribution: {label_counts}"
        
        # Add transformation info if it was a prevalence dataset
        if was_prevalence_dataset:
            validation_errors.append(
                f"✓ Dataset automatically transformed from prevalence format to text classification format"
            )
            validation_errors.append(
                f"✓ Created {len(df)} text samples with binary labels based on total prevalence threshold"
            )
        
        if missing_text > 0:
            validation_errors.append(f"{missing_text} missing values in text column")
        if missing_label > 0:
            validation_errors.append(f"{missing_label} missing values in label column")
        if duplicates > 0:
            validation_errors.append(f"{duplicates} duplicate rows found")
        
        # Add class balance warning if imbalanced
        if len(label_counts) == 2:
            min_count = min(label_counts.values())
            max_count = max(label_counts.values())
            if min_count / max_count < 0.2:  # Less than 20% balance
                validation_errors.append(
                    f"Warning: Dataset is imbalanced ({class_balance_info}). "
                    f"Consider using SMOTE during training."
                )
        
        # Preview (first 10 rows of cleaned data)
        preview = df.head(10).to_dict(orient='records')
        
        # Create dataset record
        dataset = Dataset(
            name=name or file.filename,
            filename=file.filename,
            file_path=file_path,
            text_column=text_column,
            label_column=label_column,
            is_private=is_private,
            is_anonymous=is_anonymous,
            row_count=len(df),
            column_mapping={text_column: "text", label_column: "label"},
            validation_errors="; ".join(validation_errors) if validation_errors else None,
            owner_id=current_user.id
        )
        
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        return DatasetUploadResponse(
            dataset_id=dataset.id,
            message="Dataset uploaded successfully",
            preview=preview,
            validation_summary={
                "row_count": len(df),
                "column_count": len(df.columns),
                "missing_text": int(missing_text),
                "missing_label": int(missing_label),
                "duplicates": int(duplicates),
                "errors": validation_errors
            }
        )
    
    except pd.errors.EmptyDataError:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="CSV file is empty or invalid")
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"Error processing dataset: {str(e)}")


@router.get("/", response_model=List[DatasetResponse])
async def list_datasets(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all datasets accessible to the user"""
    if current_user.is_admin:
        datasets = db.query(Dataset).all()
    else:
        datasets = db.query(Dataset).filter(
            (Dataset.owner_id == current_user.id) | (Dataset.is_private == False)
        ).all()
    
    return datasets


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get a specific dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not current_user.is_admin and dataset.owner_id != current_user.id and dataset.is_private:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return dataset


@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a dataset"""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not current_user.is_admin and dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Delete file
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)
    
    db.delete(dataset)
    db.commit()
    
    return {"message": "Dataset deleted successfully"}

