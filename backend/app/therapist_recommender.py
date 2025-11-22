"""
AI Therapist-Style Q&A and Personalized Wellbeing Plan Generator
Hybrid ML + Rule-based system for supportive mental wellbeing guidance
"""
import re
import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict
import logging

# Try to import transformers for better NLP, fallback to sklearn
try:
    from transformers import pipeline as transformers_pipeline
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Dynamic question generator - exact 10 questions in order"""
    
    # Exact 10 questions in order
    QUESTIONS = [
        {
            "id": "q1",
            "question": "How have you been feeling emotionally lately?",
            "type": "text",
            "category": "emotional_state"
        },
        {
            "id": "q2",
            "question": "What has been stressing or worrying you the most recently?",
            "type": "text",
            "category": "stressors"
        },
        {
            "id": "q3",
            "question": "On a scale of 1–10, how would you rate your stress level right now?",
            "type": "scale",
            "scale_range": (1, 10),
            "category": "stress_level"
        },
        {
            "id": "q4",
            "question": "How well have you been sleeping in the past few days?",
            "type": "text",
            "category": "sleep"
        },
        {
            "id": "q5",
            "question": "Have you noticed any changes in your mood, appetite, or energy levels?",
            "type": "text",
            "category": "physical_changes"
        },
        {
            "id": "q6",
            "question": "Do you find it easy or difficult to focus on studies/work/tasks?",
            "type": "text",
            "category": "focus"
        },
        {
            "id": "q7",
            "question": "When you start feeling low or stressed, how do you usually cope?",
            "type": "text",
            "category": "coping"
        },
        {
            "id": "q8",
            "question": "Are you currently facing pressure from studies, work, family, or relationships?",
            "type": "text",
            "category": "pressure"
        },
        {
            "id": "q9",
            "question": "Do you have someone you can talk to or feel emotionally supported by?",
            "type": "text",
            "category": "support"
        },
        {
            "id": "q10",
            "question": "If you could improve one thing in your life right now, what would it be?",
            "type": "text",
            "category": "improvement"
        }
    ]
    
    @staticmethod
    def get_first_question() -> Dict[str, Any]:
        """Get the very first question"""
        return QuestionGenerator.QUESTIONS[0]
    
    @staticmethod
    def get_next_question(
        answered_questions: Dict[str, Any],
        last_question_id: str,
        last_answer: Any
    ) -> Optional[Dict[str, Any]]:
        """Get the next question in sequence - simple linear flow"""
        # Find current question index
        current_index = None
        for idx, q in enumerate(QuestionGenerator.QUESTIONS):
            if q["id"] == last_question_id:
                current_index = idx
                break
        
        if current_index is None:
            # If question not found, start from beginning
            return QuestionGenerator.QUESTIONS[0]
        
        # Get next question
        next_index = current_index + 1
        if next_index < len(QuestionGenerator.QUESTIONS):
            return QuestionGenerator.QUESTIONS[next_index]
        
        # All questions answered
        return None
    
    @staticmethod
    def get_total_questions() -> int:
        """Get total number of questions"""
        return len(QuestionGenerator.QUESTIONS)
    
    @staticmethod
    def get_question_by_index(index: int) -> Optional[Dict[str, Any]]:
        """Get question by index"""
        if 0 <= index < len(QuestionGenerator.QUESTIONS):
            return QuestionGenerator.QUESTIONS[index]
        return None
    


class SentimentAnalyzer:
    """NLP-based sentiment and emotion analysis"""
    
    def __init__(self):
        self.sentiment_pipeline = None
        self.emotion_pipeline = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize NLP models"""
        if TRANSFORMERS_AVAILABLE:
            try:
                # Use lightweight models
                self.sentiment_pipeline = transformers_pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1  # CPU
                )
                logger.info("Loaded transformers sentiment model")
            except Exception as e:
                logger.warning(f"Could not load transformers model: {e}")
                self._initialize_fallback()
        else:
            self._initialize_fallback()
    
    def _initialize_fallback(self):
        """Fallback to simple rule-based sentiment"""
        logger.info("Using rule-based sentiment analysis")
        self.sentiment_pipeline = None
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment and emotions from text"""
        if not text or len(text.strip()) == 0:
            return {
                "sentiment": "neutral",
                "sentiment_score": 0.5,
                "emotions": {},
                "keywords": []
            }
        
        # Use transformers if available
        if self.sentiment_pipeline:
            try:
                result = self.sentiment_pipeline(text[:512])  # Limit length
                sentiment_label = result[0]["label"].lower()
                sentiment_score = result[0]["score"]
                
                # Normalize to 0-1 scale (positive = higher, negative = lower)
                if "negative" in sentiment_label:
                    normalized_score = 1.0 - sentiment_score
                else:
                    normalized_score = sentiment_score
                
                return {
                    "sentiment": sentiment_label,
                    "sentiment_score": float(normalized_score),
                    "emotions": self._extract_emotions(text),
                    "keywords": self._extract_keywords(text)
                }
            except Exception as e:
                logger.warning(f"Transformers analysis failed: {e}")
                return self._rule_based_analysis(text)
        else:
            return self._rule_based_analysis(text)
    
    def _rule_based_analysis(self, text: str) -> Dict[str, Any]:
        """Rule-based sentiment analysis fallback"""
        text_lower = text.lower()
        
        # Sentiment keywords
        positive_words = [
            "good", "great", "happy", "fine", "okay", "well", "better",
            "improving", "positive", "hopeful", "grateful", "content"
        ]
        negative_words = [
            "bad", "sad", "depressed", "anxious", "worried", "stressed",
            "tired", "hopeless", "overwhelmed", "frustrated", "angry",
            "lonely", "scared", "nervous", "exhausted"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words > 0:
            sentiment_score = 0.5 + (positive_count - negative_count) * 0.1
            sentiment_score = max(0.0, min(1.0, sentiment_score))
        else:
            sentiment_score = 0.5
        
        sentiment = "positive" if sentiment_score > 0.6 else "negative" if sentiment_score < 0.4 else "neutral"
        
        return {
            "sentiment": sentiment,
            "sentiment_score": float(sentiment_score),
            "emotions": self._extract_emotions(text),
            "keywords": self._extract_keywords(text)
        }
    
    def _extract_emotions(self, text: str) -> Dict[str, float]:
        """Extract emotion scores from text"""
        text_lower = text.lower()
        
        emotion_keywords = {
            "anxiety": ["anxious", "worried", "nervous", "stressed", "panic", "fear"],
            "sadness": ["sad", "depressed", "down", "low", "hopeless", "empty"],
            "anger": ["angry", "frustrated", "irritated", "annoyed", "mad"],
            "joy": ["happy", "joyful", "excited", "pleased", "content", "grateful"],
            "fear": ["scared", "afraid", "worried", "nervous", "anxious"],
            "tiredness": ["tired", "exhausted", "drained", "fatigued", "worn out"]
        }
        
        emotions = {}
        for emotion, keywords in emotion_keywords.items():
            count = sum(1 for keyword in keywords if keyword in text_lower)
            if count > 0:
                emotions[emotion] = min(1.0, count * 0.3)
        
        return emotions
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords"""
        # Simple keyword extraction (can be enhanced)
        words = re.findall(r'\b[a-z]{4,}\b', text.lower())
        # Filter common stop words
        stop_words = {"that", "this", "with", "from", "have", "been", "were", "what", "when", "where", "which"}
        keywords = [w for w in words if w not in stop_words]
        return list(set(keywords))[:10]  # Top 10 unique keywords


class WellbeingScorer:
    """Calculate wellbeing scores from collected data"""
    
    @staticmethod
    def _safe_numeric(value: Any, default: float = 5.0) -> float:
        """Safely convert value to numeric, handling various types"""
        if value is None:
            return default
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, str):
            # Try to convert string to number
            try:
                return float(value)
            except (ValueError, TypeError):
                # For multiple choice strings, return default
                return default
        return default
    
    @staticmethod
    def calculate_scores(
        answers: Dict[str, Any],
        text_analysis: Dict[str, Any]
    ) -> Dict[str, float]:
        """Calculate various wellbeing scores"""
        scores = {}
        
        # Sleep score (0-10 scale, inverted: higher sleep quality = lower risk)
        sleep_score = WellbeingScorer._safe_numeric(answers.get("sleep"), 5.0)
        scores["sleep_quality"] = 1.0 - (sleep_score / 10.0)  # Inverted
        
        # Mood score (0-10 scale, higher = worse)
        mood_score = WellbeingScorer._safe_numeric(answers.get("mood"), 5.0)
        scores["mood_risk"] = mood_score / 10.0
        
        # Stress score (from multiple sources)
        stress_indicators = []
        if "stress" in answers:
            stress_val = WellbeingScorer._safe_numeric(answers["stress"], 5.0)
            stress_indicators.append(stress_val / 10.0)
        if "worry" in answers:
            worry_val = WellbeingScorer._safe_numeric(answers["worry"], 5.0)
            stress_indicators.append(worry_val / 10.0)
        if "academic_work" in answers:
            academic_val = answers["academic_work"]
            if isinstance(academic_val, bool):
                stress_indicators.append(0.7 if academic_val else 0.3)
            else:
                # Convert to bool if it's a string like "Yes"/"No"
                academic_bool = str(academic_val).lower() in ["yes", "true", "1"]
                stress_indicators.append(0.7 if academic_bool else 0.3)
        
        scores["stress_level"] = np.mean(stress_indicators) if stress_indicators else 0.5
        
        # Support score (inverted: more support = lower risk)
        support_val = answers.get("support", False)
        if isinstance(support_val, bool):
            support_score = 1.0 if support_val else 0.0
        else:
            # Convert string to bool
            support_bool = str(support_val).lower() in ["yes", "true", "1"]
            support_score = 1.0 if support_bool else 0.0
        scores["support_risk"] = 1.0 - support_score
        
        # Physical activity score (inverted)
        activity_score = WellbeingScorer._safe_numeric(answers.get("physical_activity"), 5.0)
        scores["activity_level"] = 1.0 - (activity_score / 10.0)
        
        # Nutrition score (inverted)
        nutrition_score = WellbeingScorer._safe_numeric(answers.get("nutrition"), 5.0)
        scores["nutrition_quality"] = 1.0 - (nutrition_score / 10.0)
        
        # Overall wellbeing score (weighted average)
        weights = {
            "sleep_quality": 0.2,
            "mood_risk": 0.25,
            "stress_level": 0.25,
            "support_risk": 0.15,
            "activity_level": 0.075,
            "nutrition_quality": 0.075
        }
        
        overall_score = sum(scores.get(k, 0.5) * weights.get(k, 0) for k in weights.keys())
        scores["overall_wellbeing"] = overall_score
        
        # Add sentiment influence
        sentiment_score = text_analysis.get("sentiment_score", 0.5)
        scores["overall_wellbeing"] = (scores["overall_wellbeing"] * 0.8) + (sentiment_score * 0.2)
        
        return scores
    
    @staticmethod
    def get_risk_category(overall_score: float) -> str:
        """Determine risk category"""
        if overall_score >= 0.7:
            return "High"
        elif overall_score >= 0.4:
            return "Moderate"
        else:
            return "Low"


class RecommendationEngine:
    """Generate personalized wellbeing recommendations"""
    
    # Recommendation templates organized by category and risk level
    RECOMMENDATIONS = {
        "sleep": {
            "Low": [
                "Maintain your current sleep schedule",
                "Keep your bedroom cool and dark",
                "Avoid screens 1 hour before bed"
            ],
            "Moderate": [
                "Establish a consistent sleep schedule (same bedtime and wake time)",
                "Create a relaxing bedtime routine (reading, meditation, warm bath)",
                "Limit caffeine after 2 PM",
                "Keep your bedroom cool (65-68°F) and dark",
                "Avoid screens 1-2 hours before bed",
                "Try progressive muscle relaxation before sleep"
            ],
            "High": [
                "Set a strict sleep schedule and stick to it",
                "Create a comprehensive bedtime routine (30-60 minutes before bed)",
                "Eliminate caffeine completely or limit to morning only",
                "Keep bedroom temperature cool and completely dark",
                "No screens 2 hours before bed",
                "Practice deep breathing or meditation",
                "Consider keeping a sleep diary",
                "If sleep issues persist, consider consulting a healthcare provider"
            ]
        },
        "stress": {
            "Low": [
                "Continue your current stress management practices",
                "Take regular breaks during work/study"
            ],
            "Moderate": [
                "Practice deep breathing exercises (4-7-8 technique)",
                "Take 5-minute breaks every hour",
                "Try progressive muscle relaxation",
                "Set realistic goals and prioritize tasks",
                "Learn to say 'no' when overwhelmed",
                "Practice mindfulness meditation (10-15 minutes daily)"
            ],
            "High": [
                "Practice stress-reduction techniques multiple times daily",
                "Break tasks into smaller, manageable chunks",
                "Use time-blocking to organize your day",
                "Practice deep breathing (4-7-8 technique) 3-4 times daily",
                "Try guided meditation apps (Headspace, Calm)",
                "Consider talking to a counselor or therapist",
                "Identify and limit exposure to stress triggers",
                "Build in daily relaxation time (minimum 30 minutes)"
            ]
        },
        "mood": {
            "Low": [
                "Continue engaging in activities you enjoy",
                "Stay connected with supportive people"
            ],
            "Moderate": [
                "Engage in activities you enjoy daily (even for 15 minutes)",
                "Practice gratitude journaling (write 3 things daily)",
                "Spend time in nature or outdoors",
                "Connect with friends or family regularly",
                "Try new hobbies or revisit old ones",
                "Listen to uplifting music or podcasts"
            ],
            "High": [
                "Create a daily routine with enjoyable activities",
                "Practice gratitude journaling (write 5 things daily)",
                "Spend time outdoors daily (even 10 minutes)",
                "Reach out to supportive people regularly",
                "Consider professional support (counselor, therapist)",
                "Engage in creative activities (art, music, writing)",
                "Practice self-compassion and positive self-talk",
                "If mood persists, consider speaking with a healthcare provider"
            ]
        },
        "physical_activity": {
            "Low": [
                "Maintain your current activity level",
                "Try to incorporate variety in your activities"
            ],
            "Moderate": [
                "Aim for 30 minutes of moderate activity most days",
                "Start with 10-minute walks and gradually increase",
                "Find activities you enjoy (dancing, cycling, swimming)",
                "Use stairs instead of elevators when possible",
                "Take walking breaks during work/study"
            ],
            "High": [
                "Start with 10-15 minutes of activity daily",
                "Gradually build up to 30 minutes most days",
                "Choose activities you enjoy to maintain motivation",
                "Consider joining a fitness class or group",
                "Use activity tracking apps to monitor progress",
                "Remember: any movement is better than none"
            ]
        },
        "nutrition": {
            "Low": [
                "Continue your healthy eating habits",
                "Stay hydrated throughout the day"
            ],
            "Moderate": [
                "Eat regular meals (don't skip meals)",
                "Include fruits and vegetables in every meal",
                "Stay hydrated (aim for 8 glasses of water daily)",
                "Limit processed foods and added sugars",
                "Include protein in each meal for sustained energy",
                "Eat mindfully (pay attention to hunger/fullness cues)"
            ],
            "High": [
                "Establish regular meal times",
                "Plan meals ahead to avoid skipping",
                "Include mood-supportive foods: omega-3s (fish, walnuts), complex carbs (whole grains), protein",
                "Stay hydrated (carry a water bottle)",
                "Limit caffeine and alcohol",
                "Consider consulting a nutritionist",
                "Eat mindfully without distractions",
                "Keep healthy snacks available"
            ]
        },
        "social": {
            "Low": [
                "Continue nurturing your relationships",
                "Stay connected with your support network"
            ],
            "Moderate": [
                "Schedule regular check-ins with friends/family",
                "Join clubs or groups with similar interests",
                "Practice active listening in conversations",
                "Express your feelings to trusted people",
                "Offer support to others (helps build connections)"
            ],
            "High": [
                "Reach out to at least one person daily",
                "Join support groups or community activities",
                "Consider professional counseling or therapy",
                "Practice building social skills gradually",
                "Volunteer or join community groups",
                "Use online communities if in-person is difficult",
                "Remember: building connections takes time"
            ]
        },
        "general": {
            "Low": [
                "Maintain your current healthy habits",
                "Continue monitoring your wellbeing"
            ],
            "Moderate": [
                "Practice daily self-care",
                "Set aside time for relaxation",
                "Monitor your progress and adjust as needed"
            ],
            "High": [
                "Prioritize self-care daily",
                "Consider professional support",
                "Be patient with yourself - change takes time",
                "Celebrate small wins and progress"
            ]
        }
    }
    
    # Mood-supportive foods
    MOOD_FOODS = {
        "omega3": ["Salmon", "Mackerel", "Walnuts", "Flaxseeds", "Chia seeds"],
        "complex_carbs": ["Oatmeal", "Brown rice", "Quinoa", "Whole grain bread", "Sweet potatoes"],
        "protein": ["Lean chicken", "Turkey", "Eggs", "Greek yogurt", "Legumes", "Tofu"],
        "antioxidants": ["Blueberries", "Dark leafy greens", "Dark chocolate (70%+)", "Green tea"],
        "vitamin_d": ["Fatty fish", "Egg yolks", "Fortified milk", "Mushrooms"],
        "magnesium": ["Spinach", "Almonds", "Avocado", "Bananas", "Dark chocolate"]
    }
    
    @staticmethod
    def generate_plan(
        scores: Dict[str, float],
        risk_category: str,
        answers: Dict[str, Any],
        text_analysis: Dict[str, Any],
        duration: str  # "one_week", "one_month", "three_month", "six_month"
    ) -> Dict[str, Any]:
        """Generate personalized plan for given duration"""
        
        plan = {
            "daily_tasks": [],
            "lifestyle_habits": [],
            "food_suggestions": [],
            "sleep_hygiene": [],
            "stress_reduction": [],
            "physical_activity": [],
            "journaling_prompts": [],
            "screen_time": [],
            "social_connection": []
        }
        
        # Determine intensity based on duration
        if duration == "one_week":
            intensity = "moderate"
            task_count = 3
        elif duration == "one_month":
            intensity = "moderate"
            task_count = 5
        elif duration == "three_month":
            intensity = "high"
            task_count = 7
        else:  # six_month
            intensity = "high"
            task_count = 10
        
        # Generate recommendations based on scores
        if scores.get("sleep_quality", 0.5) > 0.4:
            plan["sleep_hygiene"] = RecommendationEngine.RECOMMENDATIONS["sleep"][risk_category][:task_count]
        
        if scores.get("stress_level", 0.5) > 0.4:
            plan["stress_reduction"] = RecommendationEngine.RECOMMENDATIONS["stress"][risk_category][:task_count]
        
        if scores.get("mood_risk", 0.5) > 0.4:
            plan["daily_tasks"] = RecommendationEngine.RECOMMENDATIONS["mood"][risk_category][:task_count]
        
        if scores.get("activity_level", 0.5) > 0.4:
            plan["physical_activity"] = RecommendationEngine.RECOMMENDATIONS["physical_activity"][risk_category][:task_count]
        
        if scores.get("nutrition_quality", 0.5) > 0.4:
            plan["food_suggestions"] = RecommendationEngine._get_food_recommendations(risk_category, task_count)
        
        if scores.get("support_risk", 0.5) > 0.4:
            plan["social_connection"] = RecommendationEngine.RECOMMENDATIONS["social"][risk_category][:task_count]
        
        # Add general recommendations
        plan["lifestyle_habits"] = RecommendationEngine.RECOMMENDATIONS["general"][risk_category][:task_count]
        
        # Generate journaling prompts
        plan["journaling_prompts"] = RecommendationEngine._get_journaling_prompts(risk_category, duration, task_count)
        
        # Screen time recommendations
        plan["screen_time"] = RecommendationEngine._get_screen_time_recommendations(risk_category, task_count)
        
        return plan
    
    @staticmethod
    def _get_food_recommendations(risk_category: str, count: int) -> List[str]:
        """Get food recommendations"""
        foods = []
        
        if risk_category == "High":
            # Include all categories
            for category, items in RecommendationEngine.MOOD_FOODS.items():
                foods.extend(items[:2])
        elif risk_category == "Moderate":
            # Focus on key categories
            foods.extend(RecommendationEngine.MOOD_FOODS["omega3"][:2])
            foods.extend(RecommendationEngine.MOOD_FOODS["complex_carbs"][:2])
            foods.extend(RecommendationEngine.MOOD_FOODS["protein"][:2])
        else:
            # Light recommendations
            foods.extend(RecommendationEngine.MOOD_FOODS["complex_carbs"][:2])
            foods.extend(RecommendationEngine.MOOD_FOODS["protein"][:1])
        
        return foods[:count]
    
    @staticmethod
    def _get_journaling_prompts(risk_category: str, duration: str, count: int) -> List[str]:
        """Get journaling prompts"""
        prompts = [
            "What am I grateful for today?",
            "What emotions did I experience today?",
            "What went well today?",
            "What challenged me today and how did I handle it?",
            "What did I learn about myself today?",
            "How did I take care of myself today?",
            "What would I like to improve tomorrow?",
            "Who supported me today and how?",
            "What made me smile or laugh today?",
            "How did I show kindness to myself today?",
            "What are my current worries and what can I control?",
            "What progress have I made this week?",
            "What activities energize me?",
            "What boundaries do I need to set?",
            "How can I be more compassionate with myself?"
        ]
        
        if risk_category == "High":
            return prompts[:count]
        elif risk_category == "Moderate":
            return prompts[:min(count, 7)]
        else:
            return prompts[:min(count, 5)]
    
    @staticmethod
    def _get_screen_time_recommendations(risk_category: str, count: int) -> List[str]:
        """Get screen time recommendations"""
        recommendations = []
        
        if risk_category == "High":
            recommendations = [
                "Limit screen time to 2 hours before bed",
                "Use blue light filters in the evening",
                "Take 10-minute screen breaks every hour",
                "Set specific times for checking social media",
                "Use app timers to limit usage",
                "Replace evening screen time with reading or relaxation",
                "Keep phones out of the bedroom",
                "Practice 'no phone' meals"
            ]
        elif risk_category == "Moderate":
            recommendations = [
                "Limit screen time to 1 hour before bed",
                "Take 5-minute screen breaks every hour",
                "Set boundaries for social media use",
                "Use blue light filters in the evening",
                "Replace some screen time with offline activities"
            ]
        else:
            recommendations = [
                "Maintain healthy screen time habits",
                "Take regular breaks from screens",
                "Avoid screens 30 minutes before bed"
            ]
        
        return recommendations[:count]


# Global instances
_sentiment_analyzer = None

def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get or create sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer

