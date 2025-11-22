from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.config import settings
from app.database import engine, Base
from app.routers import auth, datasets, training, predictions, admin, users, therapist

# Try to import explain router, but don't fail if XAI dependencies are missing
# This is completely optional - server will work fine without it
EXPLAIN_AVAILABLE = False
explain_router = None
try:
    from app.routers import explain
    explain_router = explain.router
    EXPLAIN_AVAILABLE = True
except Exception as e:
    # Silently ignore - explainability is optional
    EXPLAIN_AVAILABLE = False
    explain_router = None
from sqlalchemy import inspect, text

# Create database tables
Base.metadata.create_all(bind=engine)

# Add missing columns if they don't exist (migration)
def migrate_database():
    """Add missing columns to existing tables"""
    try:
        inspector = inspect(engine)
        
        # Check if training_jobs table exists
        if 'training_jobs' in inspector.get_table_names():
            with engine.begin() as conn:
                # Check if started_at column exists
                columns = [col['name'] for col in inspector.get_columns('training_jobs')]
                if 'started_at' not in columns:
                    try:
                        conn.execute(text("ALTER TABLE training_jobs ADD COLUMN started_at DATETIME"))
                        print("✓ Added started_at column to training_jobs table")
                    except Exception as e:
                        # Column might already exist or table structure issue
                        print(f"Migration note: {e}")
    except Exception as e:
        # Migration is optional, don't fail if it doesn't work
        print(f"Migration skipped: {e}")

# Run migration
migrate_database()

app = FastAPI(
    title="Digital Mental Supporter API",
    description="API for mental health assessment and support",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["Datasets"])
app.include_router(training.router, prefix="/api/training", tags=["Training"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["Predictions"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(therapist.router, prefix="/api/therapist", tags=["Therapist"])

# Include explain router only if available (completely optional)
if EXPLAIN_AVAILABLE and explain_router:
    try:
        app.include_router(explain_router, prefix="/api/explain", tags=["Explainability"])
    except Exception as e:
        # If router inclusion fails, just skip it - don't break the server
        print(f"Warning: Could not include explain router: {e}")
        pass


@app.get("/api/health")
async def health_check():
    return JSONResponse({"status": "healthy", "version": "1.0.0"})


@app.get("/")
async def root():
    return {"message": "Digital Mental Supporter API"}

