from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime


# Auth schemas
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    university: Optional[str] = None
    consent_given: bool


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: str
    is_admin: bool
    university: Optional[str]
    consent_given: bool
    
    class Config:
        from_attributes = True


class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


# Dataset schemas
class DatasetCreate(BaseModel):
    name: str
    text_column: str
    label_column: str
    is_private: bool = True
    is_anonymous: bool = False
    column_mapping: Optional[Dict[str, str]] = None


class DatasetResponse(BaseModel):
    id: int
    name: str
    filename: str
    text_column: str
    label_column: str
    is_private: bool
    is_anonymous: bool
    row_count: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class DatasetUploadResponse(BaseModel):
    dataset_id: int
    message: str
    preview: List[Dict[str, Any]]
    validation_summary: Dict[str, Any]


# Training schemas
class TrainingRequest(BaseModel):
    dataset_id: int
    model_type: str = "logistic_regression"  # logistic_regression, random_forest, bert
    use_smote: bool = False


class AutoTrainingRequest(BaseModel):
    dataset_id: int
    use_smote: bool = False


class TrainingJobResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str


class TrainingStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    metrics: Optional[Dict[str, Any]] = None
    model_version: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    model_type: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None


class AutoTrainingResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    best_model: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    models_ranked: Optional[List[Dict[str, Any]]] = None
    error_message: Optional[str] = None


# Prediction schemas
class QuestionnaireInput(BaseModel):
    q1: int  # 0-4
    q2: int
    q3: int
    q4: int
    q5: int
    q6: int
    q7: int
    q8: int
    free_text: Optional[str] = ""


class FreeTextInput(BaseModel):
    text: str


class ExplanationItem(BaseModel):
    feature: str
    weight: float


class PredictionResponse(BaseModel):
    score: float
    label: str
    explanation: List[ExplanationItem]  # Changed to use proper model with feature (str) and weight (float)
    suggestions: List[str]
    is_urgent: bool
    emergency_contacts: Optional[List[Dict[str, str]]] = None


# Admin schemas
class AnalyticsResponse(BaseModel):
    total_uploads: int
    total_trainings: int
    total_predictions: int
    label_distribution: Dict[str, int]
    average_score: float
    model_drift_alert: bool


class ModelResponse(BaseModel):
    id: int
    version: str
    model_type: str
    metrics: Dict[str, Any]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Therapist schemas
class QuestionItem(BaseModel):
    id: str
    question: str
    type: str  # scale, yes_no, multiple_choice, text
    category: Optional[str] = None
    options: Optional[List[str]] = None
    scale_range: Optional[Tuple[int, int]] = None
    parent_question: Optional[str] = None


class TherapistStartResponse(BaseModel):
    session_id: str
    questions: List[QuestionItem]
    message: str


class AnswerItem(BaseModel):
    question_id: str
    answer: Any  # Can be int, str, bool, etc.
    text_response: Optional[str] = None


class TherapistAnswerRequest(BaseModel):
    session_id: str
    answers: List[AnswerItem]


class TherapistAnswerResponse(BaseModel):
    session_id: str
    next_questions: List[QuestionItem]
    analysis: Optional[Dict[str, Any]] = None
    partial_recommendations: Optional[Dict[str, Any]] = None
    progress: float  # 0.0 to 1.0
    message: str


class WellbeingPlan(BaseModel):
    daily_tasks: List[str]
    lifestyle_habits: List[str]
    food_suggestions: List[str]
    sleep_hygiene: List[str]
    stress_reduction: List[str]
    physical_activity: List[str]
    journaling_prompts: List[str]
    screen_time: List[str]
    social_connection: List[str]


class TherapistFinalPlanResponse(BaseModel):
    session_id: str
    one_week_plan: WellbeingPlan
    one_month_plan: WellbeingPlan
    three_month_plan: WellbeingPlan
    six_month_plan: WellbeingPlan
    insights: Dict[str, Any]
    emotion_analysis: Dict[str, Any]
    risk_category: str
    wellbeing_score: float
    scores_breakdown: Dict[str, float]

