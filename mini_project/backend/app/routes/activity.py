from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..auth import get_current_user, require_parent
from ..models import User, Activity, ActivityFeedback, Child
from ..schemas import (
    ActivityOut,
    ActivityRecommendationRequest,
    ActivityRecommendationResponse,
    ActivityFeedbackCreate,
    ActivityFeedbackOut,
)
from ..llm.activity_service import generate_activity_recommendations

router = APIRouter(prefix="/api/activities", tags=["Activities"])

@router.get("", response_model=List[ActivityOut])
def get_all_activities(db: Session = Depends(get_db)):
    """Fetch stored activity catalog"""
    return db.query(Activity).all()

@router.post("/recommend", response_model=ActivityRecommendationResponse)
def get_recommendation(
    req: ActivityRecommendationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate personalized caregiver activity recommendation"""
    try:
        recommendation = generate_activity_recommendations(req.child_id, db)
        return recommendation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate recommendation: {str(e)}")

@router.post("/feedback", response_model=ActivityFeedbackOut, status_code=status.HTTP_201_CREATED)
def submit_activity_feedback(
    feedback: ActivityFeedbackCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Submit caregiver feedback for an activity"""
    db_feedback = ActivityFeedback(
        user_id=current_user.id,
        activity_id=feedback.activity_id,
        rating=feedback.rating,
        helpful=feedback.helpful,
        comment=feedback.comment
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback