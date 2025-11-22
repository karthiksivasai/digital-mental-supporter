import os
import pandas as pd
import numpy as np
import uuid
import threading
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database import get_db, SessionLocal
from app.models import Dataset, TrainingJob, Model, User
from app.schemas import TrainingRequest, TrainingJobResponse, TrainingStatusResponse, AutoTrainingRequest, AutoTrainingResponse
from app.auth import get_current_active_user
from app.ml_pipeline import MLPipeline
from app.auto_trainer import (
    preprocess_data,
    train_multiple_models,
    evaluate_models,
    select_best_model,
    save_model_and_report
)
from sklearn.model_selection import train_test_split
from datetime import datetime

router = APIRouter()

MODELS_DIR = "models"
TRAINING_JOBS = {}  # In-memory job storage (use Redis/Celery in production)
TRAINING_THREADS = {}  # Store thread references for pause/cancel


def train_model_async(job_id: str, dataset_id: int, model_type: str, use_smote: bool):
    """Background training function"""
    # Create a new database session for this thread
    db = SessionLocal()
    job = None
    try:
        # Update job status
        job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
        if not job:
            return
        
        # Check if job was cancelled/paused before starting
        if job.status in ["paused", "cancelled"]:
            return
        
        job.status = "running"
        job.progress = 0.1
        try:
            job.started_at = datetime.utcnow()
        except Exception:
            # Column might not exist yet, ignore
            pass
        db.commit()
        
        # Load dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            job.status = "failed"
            job.error_message = "Dataset not found"
            db.commit()
            return
        
        if not os.path.exists(dataset.file_path):
            job.status = "failed"
            job.error_message = "Dataset file not found"
            db.commit()
            return
        
        job.progress = 0.2
        db.commit()
        
        # Check for pause/cancel
        db.refresh(job)
        if job.status in ["paused", "cancelled"]:
            return
        
        # Load and prepare data
        df = pd.read_csv(dataset.file_path)
        pipeline = MLPipeline(model_type=model_type)
        
        job.progress = 0.4
        db.commit()
        
        # Check for pause/cancel
        db.refresh(job)
        if job.status in ["paused", "cancelled"]:
            return
        
        try:
            X, y = pipeline.prepare_data(df, dataset.text_column, dataset.label_column, dataset.is_anonymous)
        except ValueError as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            return
        except Exception as e:
            job.status = "failed"
            job.error_message = f"Error preparing data: {str(e)}"
            db.commit()
            return
        
        if len(X) < 50:
            job.status = "failed"
            job.error_message = "Insufficient data for training (minimum 50 rows required)"
            db.commit()
            return
        
        # Check class balance
        unique_labels, counts = np.unique(y, return_counts=True)
        if len(unique_labels) < 2:
            job.status = "failed"
            class_value = unique_labels[0]
            class_count = counts[0]
            job.error_message = (
                f"❌ Training Failed: Single Class Dataset\n\n"
                f"Problem: Dataset contains only one class ({class_value}).\n"
                f"Found {class_count} samples, all with label {class_value}.\n\n"
                f"Binary classification requires at least 2 classes.\n\n"
                f"To fix this:\n"
                f"  1. Check your dataset CSV file\n"
                f"  2. Ensure the label column has at least 2 different values\n"
                f"  3. For binary classification, use 0 and 1\n"
                f"  4. Re-upload the corrected dataset\n\n"
                f"Example format:\n"
                f"  text,label\n"
                f"  'sample text 1',0\n"
                f"  'sample text 2',1\n"
                f"  'sample text 3',0\n"
                f"  'sample text 4',1"
            )
            db.commit()
            return
        
        # Check if classes are too imbalanced (warn but don't fail)
        min_class_ratio = min(counts) / max(counts)
        if min_class_ratio < 0.1:  # Less than 10% of majority class
            # This is just a warning, training can continue
            pass
        
        job.progress = 0.5
        db.commit()
        
        # Check for pause/cancel
        db.refresh(job)
        if job.status in ["paused", "cancelled"]:
            return
        
        # Build and train pipeline
        pipeline.build_pipeline(use_smote=use_smote)
        metrics = pipeline.train(X, y)
        
        # Check for pause/cancel before saving
        db.refresh(job)
        if job.status in ["paused", "cancelled"]:
            return
        
        job.progress = 0.8
        db.commit()
        
        # Save model
        os.makedirs(MODELS_DIR, exist_ok=True)
        version = f"{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        model_path = os.path.join(MODELS_DIR, f"{version}.pkl")
        
        metadata = {
            "dataset_id": dataset_id,
            "training_date": datetime.now().isoformat(),
            "metrics": metrics,
            "row_count": len(X)
        }
        
        pipeline.save_model(model_path, version, metadata)
        
        job.progress = 1.0
        job.status = "completed"
        job.metrics = metrics
        job.model_path = model_path
        job.model_version = version
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Deactivate all previous models
        db.query(Model).update({"is_active": False})
        
        # Create model record and set as active
        model = Model(
            version=version,
            model_type=model_type,
            model_path=model_path,
            training_job_id=job.id,
            dataset_id=dataset_id,
            metrics=metrics,
            is_active=True  # Automatically activate the newly trained model
        )
        db.add(model)
        db.commit()
        
        TRAINING_JOBS[job_id] = {
            "status": "completed",
            "progress": 1.0,
            "metrics": metrics,
            "version": version
        }
    
    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        TRAINING_JOBS[job_id] = {
            "status": "failed",
            "progress": 0.0,
            "error": str(e)
        }
    finally:
        db.close()


@router.post("/start", response_model=TrainingJobResponse)
async def start_training(
    request: TrainingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a training job"""
    # Check if there's already an active training job
    if current_user.is_admin:
        active_jobs = db.query(TrainingJob).filter(
            TrainingJob.status.in_(["pending", "running"])
        ).count()
    else:
        active_jobs = db.query(TrainingJob).join(Dataset).filter(
            Dataset.owner_id == current_user.id,
            TrainingJob.status.in_(["pending", "running"])
        ).count()
    
    if active_jobs > 0:
        raise HTTPException(
            status_code=400, 
            detail="Another training job is already in progress. Please wait for it to complete or cancel it first."
        )
    
    # Verify dataset exists and user has access
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not current_user.is_admin and dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create training job
    job_id = str(uuid.uuid4())
    job = TrainingJob(
        job_id=job_id,
        dataset_id=request.dataset_id,
        model_type=request.model_type,
        status="pending",
        progress=0.0
    )
    
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create training job: {str(e)}"
        )
    
    # Start training in background thread
    try:
        thread = threading.Thread(
            target=train_model_async,
            args=(job_id, request.dataset_id, request.model_type, request.use_smote)
        )
        thread.daemon = True
        thread.start()
        
        TRAINING_JOBS[job_id] = {
            "status": "pending",
            "progress": 0.0
        }
        TRAINING_THREADS[job_id] = thread
        
        return TrainingJobResponse(
            job_id=job_id,
            status="pending",
            progress=0.0,
            message="Training job started"
        )
    except Exception as e:
        # If thread creation fails, mark job as failed
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start training thread: {str(e)}"
        )


@router.get("/{job_id}/status", response_model=TrainingStatusResponse)
async def get_training_status(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get training job status"""
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check access
    if not current_user.is_admin and job.dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Calculate elapsed time and estimated remaining time
    elapsed_seconds = None
    estimated_remaining_seconds = None
    
    if job.started_at:
        elapsed_seconds = (datetime.utcnow() - job.started_at).total_seconds()
        if job.progress > 0 and job.status == "running":
            # Estimate remaining time based on progress
            estimated_total_seconds = elapsed_seconds / job.progress
            estimated_remaining_seconds = max(0, estimated_total_seconds - elapsed_seconds)
    
    return TrainingStatusResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        metrics=job.metrics,
        model_version=job.model_version,
        error_message=job.error_message,
        created_at=job.training_date,
        started_at=job.started_at,
        completed_at=job.completed_at,
        model_type=job.model_type,
        elapsed_seconds=elapsed_seconds,
        estimated_remaining_seconds=estimated_remaining_seconds
    )


@router.get("/jobs", response_model=List[TrainingStatusResponse])
async def list_training_jobs(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """List all training jobs"""
    if current_user.is_admin:
        jobs = db.query(TrainingJob).order_by(TrainingJob.training_date.desc()).limit(50).all()
    else:
        jobs = db.query(TrainingJob).join(Dataset).filter(
            Dataset.owner_id == current_user.id
        ).order_by(TrainingJob.training_date.desc()).limit(50).all()
    
    # Convert TrainingJob to TrainingStatusResponse format
    result = []
    for job in jobs:
        # Calculate elapsed time and estimated remaining time
        elapsed_seconds = None
        estimated_remaining_seconds = None
        
        if job.started_at:
            elapsed_seconds = (datetime.utcnow() - job.started_at).total_seconds()
            if job.progress > 0 and job.status == "running":
                # Estimate remaining time based on progress
                estimated_total_seconds = elapsed_seconds / job.progress
                estimated_remaining_seconds = max(0, estimated_total_seconds - elapsed_seconds)
        
        result.append(TrainingStatusResponse(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            metrics=job.metrics,
            model_version=job.model_version,
            error_message=job.error_message,
            created_at=job.training_date,
            started_at=job.started_at,
            completed_at=job.completed_at,
            model_type=job.model_type,
            elapsed_seconds=elapsed_seconds,
            estimated_remaining_seconds=estimated_remaining_seconds
        ))
    
    return result


@router.post("/{job_id}/pause")
async def pause_training(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Pause a training job"""
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check access
    if not current_user.is_admin and job.dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Only pause if job is pending or running
    if job.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot pause job with status: {job.status}"
        )
    
    job.status = "paused"
    db.commit()
    
    return {"message": "Training job paused", "status": "paused"}


@router.post("/{job_id}/cancel")
async def cancel_training(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Cancel a training job"""
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check access
    if not current_user.is_admin and job.dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Only cancel if job is pending, running, or paused
    if job.status in ["completed", "failed", "cancelled"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel job with status: {job.status}"
        )
    
    job.status = "cancelled"
    job.error_message = "Training cancelled by user"
    db.commit()
    
    # Clean up thread reference
    if job_id in TRAINING_THREADS:
        del TRAINING_THREADS[job_id]
    
    return {"message": "Training job cancelled", "status": "cancelled"}


def auto_train_models_async(job_id: str, dataset_id: int, use_smote: bool):
    """Background auto-training function"""
    db = SessionLocal()
    job = None
    try:
        job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
        if not job:
            return
        
        if job.status in ["paused", "cancelled"]:
            return
        
        job.status = "running"
        job.progress = 0.05
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Load dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            job.status = "failed"
            job.error_message = "Dataset not found"
            db.commit()
            return
        
        if not os.path.exists(dataset.file_path):
            job.status = "failed"
            job.error_message = "Dataset file not found"
            db.commit()
            return
        
        job.progress = 0.1
        db.commit()
        
        # Load and preprocess data
        df = pd.read_csv(dataset.file_path)
        
        job.progress = 0.2
        db.commit()
        
        # Preprocess data
        try:
            X, y, preprocessing_info = preprocess_data(
                df, dataset.text_column, dataset.label_column, dataset.is_anonymous
            )
        except ValueError as e:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
            return
        except Exception as e:
            job.status = "failed"
            job.error_message = f"Error preprocessing data: {str(e)}"
            db.commit()
            return
        
        if len(X) < 50:
            job.status = "failed"
            job.error_message = "Insufficient data for training (minimum 50 rows required)"
            db.commit()
            return
        
        # Check for pause/cancel
        db.refresh(job)
        if job.status in ["paused", "cancelled"]:
            return
        
        job.progress = 0.3
        db.commit()
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        job.progress = 0.4
        db.commit()
        
        # Progress callback for model training
        def progress_callback(message: str):
            db.refresh(job)
            if job.status in ["paused", "cancelled"]:
                return
            # Update progress incrementally during model training
            current_progress = job.progress
            if current_progress < 0.9:
                job.progress = min(current_progress + 0.1, 0.9)
                db.commit()
        
        # Train multiple models
        models_results = train_multiple_models(
            X_train, y_train, X_test, y_test,
            use_smote=use_smote,
            progress_callback=progress_callback
        )
        
        # Check for pause/cancel
        db.refresh(job)
        if job.status in ["paused", "cancelled"]:
            return
        
        job.progress = 0.9
        db.commit()
        
        # Evaluate models
        evaluation = evaluate_models(models_results)
        
        # Select best model
        best_model_name, best_model_result = select_best_model(models_results, evaluation)
        
        # Save models and report
        saved_paths = save_model_and_report(
            best_model_name,
            best_model_result,
            models_results,
            evaluation,
            preprocessing_info,
            dataset_id,
            MODELS_DIR,
            os.path.join(MODELS_DIR, "history")
        )
        
        # Calculate total training time
        total_time = sum(r.get("training_time", 0.0) for r in models_results.values())
        
        # Prepare response data
        models_ranked = sorted(
            [
                {
                    "model": name,
                    "f1": result.get("metrics", {}).get("f1", 0.0),
                    "accuracy": result.get("metrics", {}).get("accuracy", 0.0),
                    "precision": result.get("metrics", {}).get("precision", 0.0),
                    "recall": result.get("metrics", {}).get("recall", 0.0),
                    "training_time": result.get("training_time", 0.0),
                    "status": "success" if "error" not in result else "failed"
                }
                for name, result in models_results.items()
            ],
            key=lambda x: (x["f1"], x["accuracy"]),
            reverse=True
        )
        
        # Update job status
        job.progress = 1.0
        job.status = "completed"
        job.metrics = best_model_result["metrics"]
        job.model_path = saved_paths["best_model_path"]
        job.model_version = f"auto_{best_model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        job.completed_at = datetime.utcnow()
        db.commit()
        
        # Deactivate all previous models
        db.query(Model).update({"is_active": False})
        
        # Create model record for best model
        model = Model(
            version=job.model_version,
            model_type=best_model_name,
            model_path=saved_paths["best_model_path"],
            training_job_id=job.id,
            dataset_id=dataset_id,
            metrics=best_model_result["metrics"],
            is_active=True
        )
        db.add(model)
        db.commit()
        
        TRAINING_JOBS[job_id] = {
            "status": "completed",
            "progress": 1.0,
            "metrics": best_model_result["metrics"],
            "best_model": best_model_name,
            "models_ranked": models_ranked
        }
    
    except Exception as e:
        if job:
            job.status = "failed"
            job.error_message = str(e)
            db.commit()
        TRAINING_JOBS[job_id] = {
            "status": "failed",
            "progress": 0.0,
            "error": str(e)
        }
    finally:
        db.close()


@router.post("/auto", response_model=AutoTrainingResponse)
async def auto_train_models(
    request: AutoTrainingRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Auto train multiple models and select the best one"""
    # Check if there's already an active training job
    if current_user.is_admin:
        active_jobs = db.query(TrainingJob).filter(
            TrainingJob.status.in_(["pending", "running"])
        ).count()
    else:
        active_jobs = db.query(TrainingJob).join(Dataset).filter(
            Dataset.owner_id == current_user.id,
            TrainingJob.status.in_(["pending", "running"])
        ).count()
    
    if active_jobs > 0:
        raise HTTPException(
            status_code=400,
            detail="Another training job is already in progress. Please wait for it to complete or cancel it first."
        )
    
    # Verify dataset exists and user has access
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    if not current_user.is_admin and dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create training job
    job_id = str(uuid.uuid4())
    job = TrainingJob(
        job_id=job_id,
        dataset_id=request.dataset_id,
        model_type="auto_training",  # Special type for auto-training
        status="pending",
        progress=0.0
    )
    
    try:
        db.add(job)
        db.commit()
        db.refresh(job)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create training job: {str(e)}"
        )
    
    # Start auto-training in background thread
    try:
        thread = threading.Thread(
            target=auto_train_models_async,
            args=(job_id, request.dataset_id, request.use_smote)
        )
        thread.daemon = True
        thread.start()
        
        TRAINING_JOBS[job_id] = {
            "status": "pending",
            "progress": 0.0
        }
        TRAINING_THREADS[job_id] = thread
        
        return AutoTrainingResponse(
            job_id=job_id,
            status="pending",
            progress=0.0,
            message="Auto-training started. Training multiple models..."
        )
    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start auto-training thread: {str(e)}"
        )


@router.get("/auto/{job_id}/results", response_model=AutoTrainingResponse)
async def get_auto_training_results(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get auto-training results"""
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check access
    if not current_user.is_admin and job.dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Load metrics report if available
    report_path = os.path.join(MODELS_DIR, "metrics_report.json")
    models_ranked = []
    best_model = None
    
    if os.path.exists(report_path):
        try:
            import json
            with open(report_path, 'r') as f:
                report = json.load(f)
                models_ranked = report.get("models_ranked", [])
                best_model = report.get("best_model")
        except:
            pass
    
    # If job is completed, get best model from job data
    if job.status == "completed" and job_id in TRAINING_JOBS:
        job_data = TRAINING_JOBS[job_id]
        models_ranked = job_data.get("models_ranked", models_ranked)
        best_model = job_data.get("best_model", best_model)
    
    return AutoTrainingResponse(
        job_id=job.job_id,
        status=job.status,
        progress=job.progress,
        message="Auto-training completed" if job.status == "completed" else f"Status: {job.status}",
        best_model=best_model,
        metrics=job.metrics,
        models_ranked=models_ranked,
        error_message=job.error_message
    )


@router.get("/metrics-report")
async def get_metrics_report(
    current_user: User = Depends(get_current_active_user),
):
    """Download the metrics report JSON file"""
    report_path = os.path.join(MODELS_DIR, "metrics_report.json")
    if not os.path.exists(report_path):
        raise HTTPException(status_code=404, detail="Metrics report not found")
    
    return FileResponse(
        report_path,
        media_type="application/json",
        filename="metrics_report.json"
    )


@router.delete("/{job_id}")
async def delete_training_job(
    job_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete a training job"""
    job = db.query(TrainingJob).filter(TrainingJob.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Check access
    if not current_user.is_admin and job.dataset.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Cancel if still running
    if job.status in ["pending", "running", "paused"]:
        job.status = "cancelled"
        job.error_message = "Training job deleted"
        db.commit()
    
    # Delete associated model file if exists
    if job.model_path and os.path.exists(job.model_path):
        try:
            os.remove(job.model_path)
        except Exception:
            pass  # Ignore file deletion errors
    
    # Delete model record if exists
    model = db.query(Model).filter(Model.training_job_id == job.id).first()
    if model:
        db.delete(model)
    
    # Delete the job
    db.delete(job)
    db.commit()
    
    # Clean up references
    if job_id in TRAINING_JOBS:
        del TRAINING_JOBS[job_id]
    if job_id in TRAINING_THREADS:
        del TRAINING_THREADS[job_id]
    
    return {"message": "Training job deleted successfully"}

