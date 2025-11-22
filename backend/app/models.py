from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import json


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    university = Column(String, nullable=True)
    consent_given = Column(Boolean, default=False)
    consent_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    datasets = relationship("Dataset", back_populates="owner")
    predictions = relationship("Prediction", back_populates="user")
    therapist_sessions = relationship("TherapistSession")


class Dataset(Base):
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    text_column = Column(String, nullable=False)
    label_column = Column(String, nullable=False)
    is_private = Column(Boolean, default=True)
    is_anonymous = Column(Boolean, default=False)
    row_count = Column(Integer, default=0)
    column_mapping = Column(JSON, nullable=True)
    validation_errors = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    owner = relationship("User", back_populates="datasets")
    training_jobs = relationship("TrainingJob", back_populates="dataset")


class TrainingJob(Base):
    __tablename__ = "training_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    model_type = Column(String, default="logistic_regression")  # logistic_regression, random_forest, bert
    status = Column(String, default="pending")  # pending, running, completed, failed, paused, cancelled
    progress = Column(Float, default=0.0)
    metrics = Column(JSON, nullable=True)
    model_path = Column(String, nullable=True)
    model_version = Column(String, nullable=True)
    training_date = Column(DateTime, server_default=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    dataset = relationship("Dataset", back_populates="training_jobs")


class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, index=True)
    version = Column(String, unique=True, index=True, nullable=False)
    model_type = Column(String, nullable=False)
    model_path = Column(String, nullable=False)
    training_job_id = Column(Integer, ForeignKey("training_jobs.id"), nullable=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    metrics = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class Prediction(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_guest = Column(Boolean, default=False)
    input_data = Column(JSON, nullable=False)
    score = Column(Float, nullable=False)
    label = Column(String, nullable=False)  # Low, Moderate, High
    explanation = Column(JSON, nullable=True)
    suggestions = Column(JSON, nullable=True)
    is_urgent = Column(Boolean, default=False)
    model_version = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("User", back_populates="predictions")


class TherapistSession(Base):
    __tablename__ = "therapist_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_guest = Column(Boolean, default=False)
    status = Column(String, default="in_progress")  # in_progress, completed
    answers = Column(JSON, nullable=True)  # Store all Q&A data
    text_responses = Column(JSON, nullable=True)  # Store free-text responses
    scores = Column(JSON, nullable=True)  # Store calculated scores
    text_analysis = Column(JSON, nullable=True)  # Store NLP analysis
    wellbeing_plans = Column(JSON, nullable=True)  # Store generated plans
    risk_category = Column(String, nullable=True)
    wellbeing_score = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
    
    user = relationship("User")

