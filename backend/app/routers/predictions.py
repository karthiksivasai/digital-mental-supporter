from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models import Prediction, Model, User
from app.schemas import QuestionnaireInput, FreeTextInput, PredictionResponse
from app.auth import get_current_user, get_current_active_user
from app.ml_pipeline import MLPipeline
from app.emergency_detector import EmergencyDetector
from app.scoring import QuestionnaireScorer
from datetime import datetime
import os
import logging

router = APIRouter()


def get_active_model(db: Session) -> Optional[Model]:
    """Get the currently active model"""
    model = db.query(Model).filter(Model.is_active == True).first()
    return model


@router.post("/questionnaire", response_model=PredictionResponse)
async def predict_from_questionnaire(
    input_data: QuestionnaireInput,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict from questionnaire responses"""
    # Check for urgent keywords
    is_urgent = EmergencyDetector.detect_urgent(input_data.free_text or "", input_data.q7)
    
    # Calculate score
    responses = {
        "q1": input_data.q1,
        "q2": input_data.q2,
        "q3": input_data.q3,
        "q4": input_data.q4,
        "q5": input_data.q5,
        "q6": input_data.q6,
        "q7": input_data.q7,
        "q8": input_data.q8
    }
    
    score = QuestionnaireScorer.calculate_score(responses)
    label = QuestionnaireScorer.get_risk_label(score, is_urgent)
    
    # Override to High if urgent
    if is_urgent:
        score = 100
        label = "High"
    
    # Get suggestions
    suggestions = QuestionnaireScorer.get_suggestions(label, is_urgent)
    
    # Generate explanation (simplified - using questionnaire weights)
    explanation = []
    if input_data.q7 > 0:
        explanation.append({"feature": "self_harm_thoughts", "weight": 0.4})
    if input_data.q1 >= 3:
        explanation.append({"feature": "depression", "weight": 0.25})
    if input_data.q3 >= 3:
        explanation.append({"feature": "sleep_issues", "weight": 0.2})
    if input_data.q4 >= 3:
        explanation.append({"feature": "anxiety", "weight": 0.15})
    
    # Save prediction
    prediction = Prediction(
        user_id=current_user.id if current_user else None,
        is_guest=current_user is None,
        input_data=responses,
        score=score,
        label=label,
        explanation=explanation,
        suggestions=suggestions,
        is_urgent=is_urgent
    )
    
    db.add(prediction)
    db.commit()
    
    response = PredictionResponse(
        score=score,
        label=label,
        explanation=explanation,
        suggestions=suggestions,
        is_urgent=is_urgent
    )
    
    if is_urgent:
        response.emergency_contacts = EmergencyDetector.get_emergency_contacts()
    
    return response


@router.post("/text", response_model=PredictionResponse)
async def predict_from_text(
    input_data: FreeTextInput,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Predict from free text input"""
    try:
        # Check for urgent keywords
        is_urgent = EmergencyDetector.detect_urgent(input_data.text, 0)
        
        # Get active model
        model_record = get_active_model(db)
        
        if model_record and os.path.exists(model_record.model_path):
            try:
                # Load model and predict
                model_data = MLPipeline.load_model(model_record.model_path)
                pipeline = MLPipeline(model_type=model_data['model_type'])
                pipeline.pipeline = model_data['pipeline']
                pipeline.vectorizer = model_data['vectorizer']
                pipeline.model = model_data['model']
                pipeline.feature_names = model_data['feature_names']
                
                proba, pred = pipeline.predict(input_data.text)
                score = proba * 100
                
                # Get explanation
                explanation = pipeline.explain_prediction(input_data.text, top_n=5)
                
            except Exception as e:
                # Log error but continue with fallback
                logging.error(f"Error loading/predicting with model: {str(e)}")
                # Fallback to rule-based scoring
                text_lower = input_data.text.lower()
                negative_words = ["sad", "depressed", "anxious", "worried", "tired", "hopeless"]
                positive_words = ["happy", "good", "fine", "okay", "well"]
                
                negative_count = sum(1 for word in negative_words if word in text_lower)
                positive_count = sum(1 for word in positive_words if word in text_lower)
                
                score = min(100, max(0, 30 + (negative_count * 15) - (positive_count * 10)))
                explanation = [{"feature": "sentiment_analysis", "weight": 0.5}]
        else:
            # Fallback: simple rule-based scoring
            text_lower = input_data.text.lower()
            negative_words = ["sad", "depressed", "anxious", "worried", "tired", "hopeless"]
            positive_words = ["happy", "good", "fine", "okay", "well"]
            
            negative_count = sum(1 for word in negative_words if word in text_lower)
            positive_count = sum(1 for word in positive_words if word in text_lower)
            
            score = min(100, max(0, 30 + (negative_count * 15) - (positive_count * 10)))
            explanation = [{"feature": "sentiment_analysis", "weight": 0.5}]
        
        # Override if urgent
        if is_urgent:
            score = 100
            label = "High"
        else:
            label = QuestionnaireScorer.get_risk_label(score, is_urgent)
        
        suggestions = QuestionnaireScorer.get_suggestions(label, is_urgent)
        
        # Save prediction
        try:
            prediction = Prediction(
                user_id=current_user.id if current_user else None,
                is_guest=current_user is None,
                input_data={"text": input_data.text},
                score=score,
                label=label,
                explanation=explanation,
                suggestions=suggestions,
                is_urgent=is_urgent,
                model_version=model_record.version if model_record else None
            )
            
            db.add(prediction)
            db.commit()
        except Exception as e:
            # If saving fails, log but continue with response
            logging.error(f"Error saving prediction: {str(e)}")
            db.rollback()
        
        response = PredictionResponse(
            score=score,
            label=label,
            explanation=explanation,
            suggestions=suggestions,
            is_urgent=is_urgent
        )
        
        if is_urgent:
            response.emergency_contacts = EmergencyDetector.get_emergency_contacts()
        
        return response
    
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(f"Error in predict_from_text: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prediction: {str(e)}"
        )


@router.get("/history")
async def get_prediction_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = 20
):
    """Get user's prediction history"""
    predictions = db.query(Prediction).filter(
        Prediction.user_id == current_user.id
    ).order_by(Prediction.created_at.desc()).limit(limit).all()
    
    return predictions

