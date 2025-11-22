from typing import Dict, List


class QuestionnaireScorer:
    """Score questionnaire responses and generate suggestions"""
    
    @staticmethod
    def calculate_score(responses: Dict[str, int]) -> float:
        """Calculate score from questionnaire responses (0-100)"""
        total = sum(responses.values())
        score = int((total / 32) * 100)
        return min(100, max(0, score))
    
    @staticmethod
    def get_risk_label(score: float, is_urgent: bool = False) -> str:
        """Get risk label based on score"""
        if is_urgent:
            return "High"
        
        if score <= 24:
            return "Low"
        elif score <= 59:
            return "Moderate"
        else:
            return "High"
    
    @staticmethod
    def get_suggestions(label: str, is_urgent: bool = False) -> List[str]:
        """Get personalized suggestions based on risk level"""
        if is_urgent:
            return [
                "Immediate professional support is recommended",
                "Contact a crisis counselor or mental health professional",
                "Reach out to trusted friends or family members",
                "Call emergency services if you're in immediate danger"
            ]
        
        if label == "Low":
            return [
                "Maintain a regular daily routine",
                "Engage in 30 minutes of physical activity daily",
                "Stay connected with friends and family",
                "Track your mood for the next 2 weeks",
                "Practice mindfulness or meditation"
            ]
        elif label == "Moderate":
            return [
                "Consider scheduling a session with campus counseling services",
                "Try online counseling or teletherapy options",
                "Use mindfulness apps like Headspace or Calm",
                "Join a support group or peer counseling program",
                "Practice stress management techniques"
            ]
        else:  # High
            return [
                "Contact campus counseling services immediately",
                "Schedule an appointment with a mental health professional",
                "Reach out to trusted friends or family members",
                "Consider teletherapy for immediate support",
                "Use crisis support resources available 24/7"
            ]

