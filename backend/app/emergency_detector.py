from typing import List, Dict


class EmergencyDetector:
    """Rule-based detector for urgent mental health situations"""
    
    URGENT_KEYWORDS = [
        "kill myself", "kill myself", "suicide", "end my life", "not want to live",
        "hurt myself", "self harm", "cutting", "overdose", "jump off",
        "hang myself", "shoot myself", "no reason to live", "better off dead"
    ]
    
    HIGH_RISK_PATTERNS = [
        r"want.*die", r"end.*life", r"no.*point", r"give.*up"
    ]
    
    EMERGENCY_CONTACTS = [
        {
            "name": "National Suicide Prevention Lifeline",
            "phone": "988",
            "text": "Text HOME to 741741",
            "url": "https://988lifeline.org"
        },
        {
            "name": "Crisis Text Line",
            "phone": "741741",
            "text": "Text HOME to 741741",
            "url": "https://www.crisistextline.org"
        },
        {
            "name": "Emergency Services",
            "phone": "911",
            "text": "Call 911",
            "url": ""
        }
    ]
    
    @classmethod
    def detect_urgent(cls, text: str, q7_score: int = 0) -> bool:
        """Detect if text contains urgent keywords"""
        if q7_score > 0:
            return True
        
        text_lower = text.lower()
        for keyword in cls.URGENT_KEYWORDS:
            if keyword in text_lower:
                return True
        
        import re
        for pattern in cls.HIGH_RISK_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    @classmethod
    def get_emergency_contacts(cls) -> List[Dict[str, str]]:
        """Get emergency contact information"""
        return cls.EMERGENCY_CONTACTS

