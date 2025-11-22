import pytest
import pandas as pd
import numpy as np
from app.ml_pipeline import MLPipeline


def test_preprocess_text():
    pipeline = MLPipeline()
    assert pipeline.preprocess_text("Hello World!") == "hello world"
    assert pipeline.preprocess_text("") == ""


def test_ml_pipeline_training():
    # Create sample data
    data = {
        'text': [
            'I feel sad and depressed',
            'I am happy and excited',
            'I feel anxious and worried',
            'Everything is fine',
            'I feel terrible'
        ] * 20,  # 100 rows
        'label': [1, 0, 1, 0, 1] * 20
    }
    df = pd.DataFrame(data)
    
    pipeline = MLPipeline(model_type="logistic_regression")
    X, y = pipeline.prepare_data(df, 'text', 'label')
    
    assert len(X) > 0
    assert len(y) > 0
    
    pipeline.build_pipeline()
    metrics = pipeline.train(X, y)
    
    assert 'accuracy' in metrics
    assert 'precision' in metrics
    assert metrics['accuracy'] >= 0.0
    assert metrics['accuracy'] <= 1.0


def test_prediction():
    # Create and train a simple model
    data = {
        'text': ['sad', 'happy', 'anxious', 'good'] * 25,
        'label': [1, 0, 1, 0] * 25
    }
    df = pd.DataFrame(data)
    
    pipeline = MLPipeline(model_type="logistic_regression")
    X, y = pipeline.prepare_data(df, 'text', 'label')
    pipeline.build_pipeline()
    pipeline.train(X, y)
    
    # Test prediction
    proba, pred = pipeline.predict("I feel sad")
    assert 0.0 <= proba <= 1.0
    assert pred in [0, 1]
    
    # Test explanation
    explanation = pipeline.explain_prediction("I feel sad", top_n=3)
    assert isinstance(explanation, list)

