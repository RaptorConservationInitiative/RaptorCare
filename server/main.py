"""
RaptorCare Server
FastAPI backend for wildlife rescue station management
"""

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
import logging
from datetime import datetime, timedelta

from server.config import get_settings
from server.auth import verify_token, create_access_token
from server.database import init_db, get_db
from server.gpu import GPUPool
from server.llm import RaptorCareAI
from server.models import User, Bird
from server.schemas import (
    TokenResponse,
    BirdSchema,
    ResearchPrompt,
    ResearchOutput,
    GPUStatusResponse,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()
ai = RaptorCareAI()

# Lifespan event handlers
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🦅 RaptorCare Server starting...")
    init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("🔌 RaptorCare Server shutting down...")

# Create FastAPI app
app = FastAPI(
    title="RaptorCare API",
    description="Wildlife Rescue Station Management System",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.post("/token", response_model=TokenResponse, tags=["Auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.
    """
    # TODO: Authenticate against database
    token = create_access_token(
        data={"sub": form_data.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": token, "token_type": "bearer"}

@app.get("/health", tags=["System"])
async def health_check():
    """System health check"""
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "0.1.0"
    }

# ============================================================================
# BIRD (PATIENT) ENDPOINTS
# ============================================================================

@app.post("/birds", response_model=BirdSchema, tags=["Patients"])
async def create_bird(
    bird: BirdSchema,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create new patient record"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Implement bird creation
    return bird

@app.get("/birds/{bird_id}", response_model=BirdSchema, tags=["Patients"])
async def get_bird(
    bird_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Get patient details"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Implement bird retrieval
    return {"id": bird_id}

@app.get("/birds", tags=["Patients"])
async def list_birds(
    skip: int = 0,
    limit: int = 100,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List all patients"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Implement bird listing
    return {"birds": [], "total": 0}

# ============================================================================
# HEALTH RECORD ENDPOINTS
# ============================================================================

@app.post("/birds/{bird_id}/health-records", tags=["Health"])
async def create_health_record(
    bird_id: int,
    record_data: dict,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create daily health check record"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Implement health record creation
    return {"status": "created", "bird_id": bird_id}

# ============================================================================
# FEEDING LOG ENDPOINTS
# ============================================================================

@app.post("/birds/{bird_id}/feeding-logs", tags=["Feeding"])
async def create_feeding_log(
    bird_id: int,
    log_data: dict,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create feeding log entry"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Implement feeding log creation
    return {"status": "created", "bird_id": bird_id}

# ============================================================================
# LLM INTEGRATION ENDPOINTS
# ============================================================================

@app.post("/ai/recommendations/{bird_id}", tags=["AI"])
async def get_ai_recommendations(
    bird_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Get LLM-based care recommendations for bird"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # TODO: Implement retrieval of bird data from the database
    sample_bird = {
        "species": "Unknown",
        "weight": 0,
        "status": "Unknown",
        "behavior": "Unknown",
        "hydration_status": "Unknown",
        "days_in_care": 0,
        "injury": "Unknown",
    }

    return {
        "bird_id": bird_id,
        "recommendations": [
            "Ensure adequate hydration",
            "Monitor weight daily"
        ],
        "prognosis": "Good recovery expected"
    }

@app.post("/research/summary", response_model=ResearchOutput, tags=["Research"])
async def research_summary(
    payload: ResearchPrompt,
    token: str = Depends(oauth2_scheme)
):
    """Generate a research summary for a case or bird dataset."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    research_text = ai.generate_research_summary(
        bird_data=payload.bird_data or {},
        health_history=payload.health_history or [],
        notes=payload.research_goal or payload.notes,
    )

    return {
        "research_text": research_text,
        "gpu_used": ai.gpu_id,
        "model": settings.OLLAMA_MODEL,
    }

@app.post("/research/hypotheses", response_model=ResearchOutput, tags=["Research"])
async def research_hypotheses(
    payload: ResearchPrompt,
    token: str = Depends(oauth2_scheme)
):
    """Generate research hypotheses from bird data and trends."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    research_text = ai.generate_research_hypotheses(
        bird_data=payload.bird_data or {},
        health_history=payload.health_history or [],
    )

    return {
        "research_text": research_text,
        "gpu_used": ai.gpu_id,
        "model": settings.OLLAMA_MODEL,
    }

@app.post("/research/literature", response_model=ResearchOutput, tags=["Research"])
async def research_literature(
    payload: ResearchPrompt,
    token: str = Depends(oauth2_scheme)
):
    """Summarize research or literature text for scientific use."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not payload.notes:
        raise HTTPException(status_code=400, detail="notes field is required for literature summarization")

    research_text = ai.summarize_literature(payload.notes)
    return {
        "research_text": research_text,
        "gpu_used": ai.gpu_id,
        "model": settings.OLLAMA_MODEL,
    }

@app.get("/research/gpu-status", response_model=GPUStatusResponse, tags=["Research"])
async def research_gpu_status(token: str = Depends(oauth2_scheme)):
    """Return current GPU utilization and role assignment."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return GPUPool.get_memory_summary()

# ============================================================================
# STATUS ENDPOINTS
# ============================================================================

@app.get("/", tags=["System"])
async def root():
    """Root endpoint"""
    return {
        "name": "RaptorCare API",
        "version": "0.1.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
    )
