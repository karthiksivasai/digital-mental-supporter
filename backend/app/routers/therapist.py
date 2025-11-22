"""
AI Therapist API Router
Provides therapist-style Q&A and personalized wellbeing plans
"""
import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import TherapistSession, User
from app.schemas import (
    TherapistStartResponse,
    TherapistAnswerRequest,
    TherapistAnswerResponse,
    TherapistFinalPlanResponse,
    QuestionItem,
    WellbeingPlan
)
from app.auth import get_current_user, get_current_active_user
from app.therapist_recommender import (
    QuestionGenerator,
    get_sentiment_analyzer,
    WellbeingScorer,
    RecommendationEngine
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_or_create_session(
    session_id: Optional[str],
    user: Optional[User],
    db: Session
) -> TherapistSession:
    """Get existing session or create new one"""
    if session_id:
        session = db.query(TherapistSession).filter(
            TherapistSession.session_id == session_id
        ).first()
        if session:
            return session
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    session = TherapistSession(
        session_id=new_session_id,
        user_id=user.id if user else None,
        is_guest=user is None,
        status="in_progress",
        answers={},
        text_responses={}
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/start", response_model=TherapistStartResponse)
async def start_therapist_session(
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new therapist session
    Returns the first question only
    """
    try:
        # Create new session
        session = get_or_create_session(None, current_user, db)
        
        # Get first question only
        first_question = QuestionGenerator.get_first_question()
        
        return TherapistStartResponse(
            session_id=session.session_id,
            questions=[first_question],
            message="Welcome! I'm here to help you create a personalized wellbeing plan."
        )
    except Exception as e:
        logger.error(f"Error starting therapist session: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start session: {str(e)}"
        )


@router.post("/answer", response_model=TherapistAnswerResponse)
async def submit_answers(
    request: TherapistAnswerRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit answers to questions
    Returns next questions, analysis, and partial recommendations
    """
    try:
        # Get session
        session = db.query(TherapistSession).filter(
            TherapistSession.session_id == request.session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Update answers
        if not session.answers:
            session.answers = {}
        if not session.text_responses:
            session.text_responses = {}
        
        # Process single answer (conversational flow - one at a time)
        if len(request.answers) == 0:
            raise HTTPException(status_code=400, detail="No answers provided")
        
        # Get the single answer
        answer_item = request.answers[0]
        question_id = answer_item.question_id
        
        # Store answer
        session.answers[question_id] = answer_item.answer
        if answer_item.text_response:
            session.text_responses[question_id] = answer_item.text_response
        
        # Analyze text responses with NLP
        sentiment_analyzer = get_sentiment_analyzer()
        text_analysis = session.text_analysis or {}
        all_text = " ".join([
            resp for resp in session.text_responses.values()
            if resp and isinstance(resp, str)
        ])
        
        if all_text:
            text_analysis = sentiment_analyzer.analyze_text(all_text)
            session.text_analysis = text_analysis
        
        # Calculate scores
        scores = WellbeingScorer.calculate_scores(
            session.answers,
            text_analysis
        )
        session.scores = scores
        
        # Determine progress (exactly 10 questions)
        from app.therapist_recommender import QuestionGenerator
        total_expected = QuestionGenerator.get_total_questions()
        progress = min(1.0, len(session.answers) / total_expected)
        
        # Get next question based on last answer
        next_question = QuestionGenerator.get_next_question(
            session.answers,
            question_id,
            answer_item.answer
        )
        
        # Generate partial recommendations if enough data
        partial_recommendations = None
        if progress >= 0.5 and len(session.answers) >= 5:
            risk_category = WellbeingScorer.get_risk_category(
                scores.get("overall_wellbeing", 0.5)
            )
            partial_plan = RecommendationEngine.generate_plan(
                scores,
                risk_category,
                session.answers,
                text_analysis,
                "one_week"
            )
            partial_recommendations = {
                "preview": "Based on your responses so far, here are some initial recommendations:",
                "top_recommendations": (
                    partial_plan.get("daily_tasks", [])[:2] +
                    partial_plan.get("stress_reduction", [])[:1]
                )[:3]
            }
        
        # Save session
        db.commit()
        
        # Prepare response message
        if next_question is None:
            # No more questions - ready for final plan
            message = "Thank you for sharing all that information. I have enough details to create your personalized wellbeing plan."
        else:
            # Simple acknowledgment - let the question speak for itself
            message = ""
        
        # Prepare analysis (only if significant progress)
        analysis = None
        if progress >= 0.3:
            analysis = {
                "answered_count": len(session.answers),
                "progress_percentage": int(progress * 100)
            }
        
        return TherapistAnswerResponse(
            session_id=session.session_id,
            next_questions=[next_question] if next_question else [],
            analysis=analysis,
            partial_recommendations=partial_recommendations,
            progress=progress,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing answers: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process answers: {str(e)}"
        )


@router.post("/final-plan", response_model=TherapistFinalPlanResponse)
async def get_final_plan(
    session_id: str = Query(..., description="Session ID"),
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate final comprehensive wellbeing plan
    Returns all plans (1-week, 1-month, 3-month, 6-month)
    """
    try:
        # Get session
        session = db.query(TherapistSession).filter(
            TherapistSession.session_id == session_id
        ).first()
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Ensure we have scores
        if not session.scores:
            # Calculate scores if not already done
            text_analysis = session.text_analysis or {}
            if not text_analysis:
                # Analyze text if not done
                sentiment_analyzer = get_sentiment_analyzer()
                all_text = " ".join([
                    resp for resp in (session.text_responses or {}).values()
                    if resp and isinstance(resp, str)
                ])
                if all_text:
                    text_analysis = sentiment_analyzer.analyze_text(all_text)
                    session.text_analysis = text_analysis
            
            scores = WellbeingScorer.calculate_scores(
                session.answers or {},
                text_analysis
            )
            session.scores = scores
        else:
            scores = session.scores
        
        # Get risk category
        overall_score = scores.get("overall_wellbeing", 0.5)
        risk_category = WellbeingScorer.get_risk_category(overall_score)
        session.risk_category = risk_category
        session.wellbeing_score = overall_score
        
        # Generate all plans
        plans = {}
        for duration in ["one_week", "one_month", "three_month", "six_month"]:
            plan_data = RecommendationEngine.generate_plan(
                scores,
                risk_category,
                session.answers or {},
                session.text_analysis or {},
                duration
            )
            plans[duration] = WellbeingPlan(**plan_data)
        
        session.wellbeing_plans = {
            k: v.dict() for k, v in plans.items()
        }
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        
        # Save session
        db.commit()
        
        # Prepare insights
        insights = {
            "summary": f"Based on your responses, your overall wellbeing score is {overall_score:.1%}. "
                      f"This places you in the {risk_category} risk category.",
            "key_findings": [],
            "strengths": [],
            "areas_for_improvement": []
        }
        
        # Add key findings based on scores
        if scores.get("sleep_quality", 0.5) > 0.5:
            insights["areas_for_improvement"].append("Sleep quality could be improved")
        else:
            insights["strengths"].append("Good sleep habits")
        
        if scores.get("stress_level", 0.5) > 0.5:
            insights["areas_for_improvement"].append("Stress management needs attention")
        else:
            insights["strengths"].append("Effective stress management")
        
        if scores.get("mood_risk", 0.5) > 0.5:
            insights["areas_for_improvement"].append("Mood support is recommended")
        else:
            insights["strengths"].append("Stable mood patterns")
        
        if scores.get("support_risk", 0.5) < 0.5:
            insights["strengths"].append("Strong support network")
        else:
            insights["areas_for_improvement"].append("Building social connections could help")
        
        # Emotion analysis
        emotion_analysis = session.text_analysis or {}
        if not emotion_analysis:
            emotion_analysis = {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "emotions": {},
                "keywords": []
            }
        
        return TherapistFinalPlanResponse(
            session_id=session.session_id,
            one_week_plan=plans["one_week"],
            one_month_plan=plans["one_month"],
            three_month_plan=plans["three_month"],
            six_month_plan=plans["six_month"],
            insights=insights,
            emotion_analysis=emotion_analysis,
            risk_category=risk_category,
            wellbeing_score=overall_score,
            scores_breakdown=scores
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating final plan: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate plan: {str(e)}"
        )

