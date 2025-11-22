# AI Therapist Feature - Implementation Guide

## Overview

The AI Therapist feature is a new ML-powered module that provides therapist-style Q&A sessions and generates personalized wellbeing plans. This feature integrates seamlessly with your existing Mental Health Detection project without rebuilding anything.

## Features

✅ **Dynamic Question Generator** - Asks intelligent, therapist-style questions with follow-ups  
✅ **NLP Sentiment Analysis** - Analyzes text responses for emotions and sentiment  
✅ **ML + Rule-based Hybrid** - Combines ML predictions with rule-based recommendations  
✅ **Personalized Wellbeing Plans** - Generates 1-week, 1-month, 3-month, and 6-month plans  
✅ **Chat Interface** - Modern, user-friendly chat UI with typing animations  
✅ **PDF Export** - Download comprehensive wellbeing plans as PDF  

## Architecture

### Backend Components

1. **`therapist_recommender.py`** - Core module containing:
   - `QuestionGenerator` - Dynamic question generation with follow-up logic
   - `SentimentAnalyzer` - NLP-based sentiment and emotion analysis (with transformers fallback)
   - `WellbeingScorer` - Calculates wellbeing scores from collected data
   - `RecommendationEngine` - Generates personalized recommendations

2. **`routers/therapist.py`** - API endpoints:
   - `POST /api/therapist/start` - Start new session, get initial questions
   - `POST /api/therapist/answer` - Submit answers, get next questions
   - `POST /api/therapist/final-plan` - Generate final comprehensive plan

3. **Database Model** - `TherapistSession` table stores:
   - Session data, answers, text responses
   - Calculated scores and NLP analysis
   - Generated wellbeing plans

### Frontend Components

1. **`app/therapist/page.tsx`** - Main chat interface with:
   - Real-time chat UI
   - Question rendering (scale, yes/no, multiple choice, text)
   - Progress tracking
   - Plan display with collapsible sections
   - PDF download functionality

2. **`lib/api.ts`** - API functions:
   - `therapistApi.startSession()`
   - `therapistApi.submitAnswers()`
   - `therapistApi.getFinalPlan()`

## Installation & Setup

### 1. Database Migration

The new `TherapistSession` table will be created automatically when you start the server. No manual migration needed.

### 2. Optional: Install Transformers (for better NLP)

For enhanced sentiment analysis, you can optionally install transformers:

```bash
cd backend
pip install transformers torch
```

**Note:** The feature works without transformers - it will use rule-based sentiment analysis as a fallback.

### 3. Start the Server

```bash
# Backend
cd backend
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev
```

## Usage

### For Users

1. Navigate to **"AI Therapist"** in the navigation menu
2. The system will start asking questions automatically
3. Answer questions using:
   - **Scale (0-10)**: Use the slider
   - **Yes/No**: Click the button
   - **Multiple Choice**: Select an option
   - **Text**: Type your response
4. Continue answering questions (you can navigate between multiple questions)
5. When progress reaches ~80%, the system will generate your final plan
6. View your personalized plans and download as PDF

### API Usage Examples

#### Start a Session

```bash
POST /api/therapist/start
Authorization: Bearer <token>

Response:
{
  "session_id": "uuid",
  "questions": [
    {
      "id": "sleep",
      "question": "How has your sleep been in the last week?",
      "type": "scale",
      "scale_range": [0, 10]
    }
  ],
  "message": "Welcome! I'm here to help..."
}
```

#### Submit Answers

```bash
POST /api/therapist/answer
Authorization: Bearer <token>
{
  "session_id": "uuid",
  "answers": [
    {
      "question_id": "sleep",
      "answer": 7,
      "text_response": null
    }
  ]
}

Response:
{
  "session_id": "uuid",
  "next_questions": [...],
  "analysis": {...},
  "partial_recommendations": {...},
  "progress": 0.25,
  "message": "Thank you for sharing..."
}
```

#### Get Final Plan

```bash
POST /api/therapist/final-plan?session_id=uuid
Authorization: Bearer <token>

Response:
{
  "session_id": "uuid",
  "one_week_plan": {...},
  "one_month_plan": {...},
  "three_month_plan": {...},
  "six_month_plan": {...},
  "insights": {...},
  "emotion_analysis": {...},
  "risk_category": "Moderate",
  "wellbeing_score": 0.65,
  "scores_breakdown": {...}
}
```

## Question Flow

The system asks questions in this order:

1. **Initial Questions** (always asked):
   - Sleep quality
   - Mood/Depression
   - Stress levels

2. **Follow-up Questions** (based on answers):
   - Sleep → Bedtime, sleep duration, restfulness
   - Stress → Work pressure, coping strategies
   - Mood → Triggers, energy levels, interests

3. **Additional Core Questions** (as needed):
   - Academic/Work pressure
   - Support network
   - Future worries
   - Physical activity
   - Nutrition

## Wellbeing Plans Structure

Each plan (1-week, 1-month, 3-month, 6-month) includes:

- **Daily Tasks** - Actionable daily activities
- **Lifestyle Habits** - Long-term habit changes
- **Food Suggestions** - Mood-supportive foods
- **Sleep Hygiene** - Sleep improvement strategies
- **Stress Reduction** - Stress management techniques
- **Physical Activity** - Exercise recommendations
- **Journaling Prompts** - Reflection questions
- **Screen Time** - Digital wellness tips
- **Social Connection** - Relationship building activities

## Risk Categories

- **Low** (score < 0.4): Minimal recommendations, maintenance focus
- **Moderate** (score 0.4-0.7): Structured recommendations, regular check-ins
- **High** (score > 0.7): Comprehensive support, professional guidance suggested

## Integration with Existing System

✅ **Uses existing authentication** - Same user system  
✅ **Uses existing ML pipeline** - Can integrate with trained models  
✅ **Uses existing database** - New table added, no conflicts  
✅ **Uses existing frontend patterns** - Consistent UI/UX  

## Safety & Disclaimers

⚠️ **Important**: This feature provides **wellness guidance only**, NOT medical diagnosis or treatment.

- All recommendations are wellness-oriented
- No medication advice
- No medical diagnosis
- Encourages professional help when needed
- Safe, supportive language throughout

## Customization

### Adding New Questions

Edit `backend/app/therapist_recommender.py`:

```python
# Add to CORE_QUESTIONS dictionary
"new_category": {
    "question": "Your question here?",
    "type": "scale",  # or "yes_no", "multiple_choice", "text"
    "scale_range": (0, 10),
    "follow_ups": {
        "low": ["Follow-up for low scores"],
        "high": ["Follow-up for high scores"]
    }
}
```

### Modifying Recommendations

Edit `RecommendationEngine.RECOMMENDATIONS` dictionary in `therapist_recommender.py` to customize recommendation content.

### Adjusting Scoring Weights

Modify `WellbeingScorer.calculate_scores()` to adjust how different factors contribute to the overall score.

## Troubleshooting

### Transformers Not Available

If transformers isn't installed, the system automatically uses rule-based sentiment analysis. This is perfectly fine for most use cases.

### Questions Not Appearing

- Check browser console for errors
- Verify API endpoints are accessible
- Ensure user is authenticated

### Plans Not Generating

- Ensure at least 5-6 questions are answered
- Check that progress >= 0.8 before calling final-plan
- Verify session_id is correct

## Future Enhancements

Potential improvements:
- Integration with existing ML models for predictions
- Multi-language support
- Voice input/output
- Progress tracking over time
- Reminder notifications
- Integration with calendar apps

## Support

For issues or questions:
1. Check the API docs at `/api/docs`
2. Review error logs in backend console
3. Check browser console for frontend errors

---

**Note**: This feature is designed to be modular and non-intrusive. It doesn't modify any existing functionality and can be disabled by simply not including the router in `main.py`.

