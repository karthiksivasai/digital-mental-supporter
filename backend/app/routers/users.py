from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Prediction
from app.schemas import UserResponse
from app.auth import get_current_active_user

router = APIRouter()


@router.delete("/me/data")
async def delete_my_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete all user's own data"""
    # Delete predictions
    db.query(Prediction).filter(Prediction.user_id == current_user.id).delete()
    
    db.commit()
    
    return {"message": "Your data has been deleted"}

