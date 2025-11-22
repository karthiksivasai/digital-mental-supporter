"""
Explainable AI Router - SHAP and LIME explanations
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models import Model, Dataset, User
from app.auth import get_current_active_user, get_current_user
import os
import logging

# Try to import XAI explainer, but don't fail if dependencies are missing
XAI_AVAILABLE = False
try:
    from app.xai_explainer import XAIExplainer
    XAI_AVAILABLE = True
except Exception as e:
    # Catch all exceptions, not just ImportError
    XAI_AVAILABLE = False
    logging.warning(f"XAI features not available: {e}. Install shap and lime to enable explainability.")

router = APIRouter()

MODELS_DIR = "models"


class LocalExplanationRequest(BaseModel):
    text: str


@router.get("/global")
async def explain_global(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get global SHAP explanation for the best model
    
    Returns:
        Global feature importance and SHAP plots
    """
    if not XAI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="XAI features are not available. Please install shap and lime dependencies."
        )
    try:
        # Get the best/active model
        model_record = db.query(Model).filter(Model.is_active == True).first()
        
        if not model_record:
            # Try to use best_model.pkl directly
            best_model_path = os.path.join(MODELS_DIR, "best_model.pkl")
            if not os.path.exists(best_model_path):
                raise HTTPException(
                    status_code=404,
                    detail="No active model found. Please train a model first."
                )
        else:
            best_model_path = model_record.model_path
            if not os.path.exists(best_model_path):
                # Fallback to best_model.pkl
                best_model_path = os.path.join(MODELS_DIR, "best_model.pkl")
                if not os.path.exists(best_model_path):
                    raise HTTPException(
                        status_code=404,
                        detail="Model file not found"
                    )
        
        # Try to get dataset path for background data
        dataset_path = None
        if model_record and model_record.dataset_id:
            dataset = db.query(Dataset).filter(Dataset.id == model_record.dataset_id).first()
            if dataset and os.path.exists(dataset.file_path):
                dataset_path = dataset.file_path
        
        # Create explainer
        explainer = XAIExplainer(model_path=best_model_path)
        
        # Generate global explanation with minimal samples for faster computation
        # Reduced further for speed - can be increased if needed
        explanation = explainer.explain_global(dataset_path=dataset_path, n_features=20, max_samples=15)
        
        return JSONResponse(content=explanation)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in explain_global: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate global explanation: {str(e)}"
        )


@router.post("/local")
async def explain_local(
    request: LocalExplanationRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get local SHAP and LIME explanation for a specific prediction
    
    Args:
        request: Contains the input text to explain
        
    Returns:
        Local explanation with SHAP values and LIME explanation
    """
    if not XAI_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="XAI features are not available. Please install shap and lime dependencies."
        )
    try:
        if not request.text or not request.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text input is required"
            )
        
        # Get the best/active model
        model_record = db.query(Model).filter(Model.is_active == True).first()
        
        if not model_record:
            # Try to use best_model.pkl directly
            best_model_path = os.path.join(MODELS_DIR, "best_model.pkl")
            if not os.path.exists(best_model_path):
                raise HTTPException(
                    status_code=404,
                    detail="No active model found. Please train a model first."
                )
        else:
            best_model_path = model_record.model_path
            if not os.path.exists(best_model_path):
                # Fallback to best_model.pkl
                best_model_path = os.path.join(MODELS_DIR, "best_model.pkl")
                if not os.path.exists(best_model_path):
                    raise HTTPException(
                        status_code=404,
                        detail="Model file not found"
                    )
        
        # Create explainer
        explainer = XAIExplainer(model_path=best_model_path)
        
        # Generate local explanation
        explanation = explainer.explain_local(request.text)
        
        return JSONResponse(content=explanation)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in explain_local: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate local explanation: {str(e)}"
        )


@router.get("/health")
async def explain_health():
    """Check if explainability service is available"""
    best_model_path = os.path.join(MODELS_DIR, "best_model.pkl")
    model_exists = os.path.exists(best_model_path)
    
    return {
        "status": "available" if model_exists else "no_model",
        "model_path": best_model_path,
        "model_exists": model_exists
    }

