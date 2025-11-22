from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List
from app.database import get_db
from app.models import Dataset, TrainingJob, Model, Prediction, User
from app.schemas import AnalyticsResponse, ModelResponse
from app.auth import get_admin_user

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get admin analytics"""
    # Last 30 days
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Counts
    total_uploads = db.query(func.count(Dataset.id)).scalar()
    total_trainings = db.query(func.count(TrainingJob.id)).filter(
        TrainingJob.status == "completed"
    ).scalar()
    total_predictions = db.query(func.count(Prediction.id)).scalar()
    
    # Recent predictions
    recent_predictions = db.query(Prediction).filter(
        Prediction.created_at >= thirty_days_ago
    ).all()
    
    # Label distribution
    label_counts = {}
    for pred in recent_predictions:
        label_counts[pred.label] = label_counts.get(pred.label, 0) + 1
    
    # Average score
    avg_score_result = db.query(func.avg(Prediction.score)).filter(
        Prediction.created_at >= thirty_days_ago
    ).scalar()
    average_score = float(avg_score_result) if avg_score_result else 0.0
    
    # Model drift check (simplified)
    # Compare recent distribution vs training baseline
    model_drift_alert = False
    if recent_predictions:
        recent_high = sum(1 for p in recent_predictions if p.label == "High") / len(recent_predictions)
        # If >15% shift from expected (assuming balanced), alert
        if recent_high > 0.5:  # More than 50% high risk
            model_drift_alert = True
    
    return AnalyticsResponse(
        total_uploads=total_uploads or 0,
        total_trainings=total_trainings or 0,
        total_predictions=total_predictions or 0,
        label_distribution=label_counts,
        average_score=average_score,
        model_drift_alert=model_drift_alert
    )


@router.get("/models", response_model=List[ModelResponse])
async def list_models(
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all models"""
    models = db.query(Model).order_by(Model.created_at.desc()).all()
    return models


@router.post("/models/{model_id}/activate")
async def activate_model(
    model_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Activate a model version"""
    model = db.query(Model).filter(Model.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    
    # Deactivate all other models
    db.query(Model).update({"is_active": False})
    
    # Activate this model
    model.is_active = True
    db.commit()
    
    return {"message": f"Model {model.version} activated"}


@router.delete("/predictions/{prediction_id}")
async def delete_prediction(
    prediction_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete a prediction (for data deletion requests)"""
    prediction = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    db.delete(prediction)
    db.commit()
    
    return {"message": "Prediction deleted"}


@router.delete("/users/{user_id}/data")
async def delete_user_data(
    user_id: int,
    admin_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Delete all data for a user (GDPR compliance)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete predictions
    db.query(Prediction).filter(Prediction.user_id == user_id).delete()
    
    # Delete datasets (and files)
    datasets = db.query(Dataset).filter(Dataset.owner_id == user_id).all()
    import os
    for dataset in datasets:
        if os.path.exists(dataset.file_path):
            os.remove(dataset.file_path)
        db.delete(dataset)
    
    db.commit()
    
    return {"message": f"All data for user {user_id} deleted"}

