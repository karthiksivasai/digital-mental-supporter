# Digital Mental Supporter

A production-ready full-stack web application for mental health assessment and support using AI/ML.

## Features

- **Authentication & Onboarding**: JWT-based register/login with consent forms
- **Dataset Management**: CSV upload with validation and column mapping
- **ML Training Pipeline**: TF-IDF + Logistic Regression/Random Forest with preprocessing
- **Async Training**: Background job processing with progress tracking
- **Predictions**: Questionnaire and free-text assessment with explainability
- **Emergency Detection**: Rule-based urgent keyword detection
- **Admin Dashboard**: Analytics, model management, and monitoring
- **Safety Features**: Disclaimers, emergency contacts, data deletion

## Tech Stack

- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11
- **ML**: scikit-learn, pandas, joblib
- **Database**: PostgreSQL (SQLite for development)
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Git

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd "Degital mental Health "
```

2. Copy environment files:
```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

3. Update `backend/.env` with your settings (optional for development)

4. Start the application:
```bash
docker-compose up --build
```

5. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/api/docs

### Default Admin Credentials

- Email: `admin@example.com`
- Password: `admin123`

## Dataset Format

Upload CSV files with the following structure:

```csv
text,label
I feel sad and hopeless,0
I am doing well,1
I have trouble sleeping,0
```

- **text**: The text content to analyze
- **label**: Binary label (0 or 1) for training

The system will auto-detect columns, but you can specify them manually during upload.

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get token
- `GET /api/auth/me` - Get current user info

### Datasets
- `POST /api/datasets/upload` - Upload CSV dataset
- `GET /api/datasets/` - List datasets
- `GET /api/datasets/{id}` - Get dataset details
- `DELETE /api/datasets/{id}` - Delete dataset

### Training
- `POST /api/training/start` - Start training job
- `GET /api/training/{job_id}/status` - Get training status
- `GET /api/training/jobs` - List all jobs

### Predictions
- `POST /api/predictions/questionnaire` - Predict from questionnaire
- `POST /api/predictions/text` - Predict from free text
- `GET /api/predictions/history` - Get prediction history

### Admin
- `GET /api/admin/analytics` - Get analytics
- `GET /api/admin/models` - List models
- `POST /api/admin/models/{id}/activate` - Activate model

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
cd backend
pytest tests/
```

## Project Structure

```
.
├── backend/
│   ├── app/
│   │   ├── routers/      # API routes
│   │   ├── models.py     # Database models
│   │   ├── schemas.py    # Pydantic schemas
│   │   ├── ml_pipeline.py # ML training pipeline
│   │   └── main.py       # FastAPI app
│   ├── tests/            # Unit tests
│   └── requirements.txt
├── frontend/
│   ├── app/              # Next.js app directory
│   ├── components/       # React components
│   └── store/            # State management
├── docker-compose.yml
└── README.md
```

## Safety & Privacy

- **Consent Forms**: Required for all users
- **PII Anonymization**: Optional automatic removal of personal information
- **Data Deletion**: Users can request data deletion (GDPR compliant)
- **Disclaimers**: Prominent warnings that this is not a replacement for professional care
- **Emergency Detection**: Automatic detection of urgent keywords with immediate support resources

## Model Training

The system supports multiple model types:

1. **Logistic Regression** (default): Fast, interpretable baseline
2. **Random Forest**: Better performance on complex patterns
3. **BERT** (stub): Requires GPU resources (not implemented in baseline)

Training includes:
- Text preprocessing and cleaning
- TF-IDF vectorization
- Optional SMOTE for imbalanced data
- Model versioning and metrics tracking

## Monitoring

Admin dashboard provides:
- Total uploads, trainings, predictions
- Label distribution charts
- Average score trends
- Model drift detection
- Model version management

## License

This project is provided as-is for educational and research purposes.

## Disclaimer

**This application is not a replacement for professional mental health care.** If you or someone you know is experiencing a mental health crisis, please contact emergency services or a mental health professional immediately.

## Support

For issues or questions, please open an issue in the repository.

