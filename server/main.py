"""
RaptorCare Server
FastAPI backend for wildlife rescue station management
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import json
import logging
import shutil
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List

from server.config import get_settings
from server.auth import verify_token, create_access_token
from server.database import init_db, get_db
from server.gpu import GPUPool
from server.llm import RaptorCareAI
from server.sync import SyncManager
from server.models import User, Bird, HealthRecord, Station, FeedingLog, CalendarEvent, Media, BirdStatus, AnimalClass
from server.schemas import (
    TokenResponse,
    BirdSchema,
    BirdCreate,
    BirdUpdate,
    PatientCreate,
    PatientUpdate,
    HealthRecordCreate,
    HealthRecordSchema,
    FeedingLogCreate,
    FeedingLogSchema,
    MediaSchema,
    CalendarEventCreate,
    CalendarEventSchema,
    ResearchPrompt,
    ResearchOutput,
    GPUStatusResponse,
    StationSchema,
    StationUpdate,
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
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    logger.info(f"✅ Database initialized and upload directory ensured at {settings.UPLOAD_DIR}")
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


# ============================================================================
# STATIC UI
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent
UI_DIR = BASE_DIR / "static_ui"

app.mount(
    "/ui",
    StaticFiles(directory=str(UI_DIR), html=True),
    name="ui"
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

def _create_patient_record(record: BirdCreate, db):
    new_bird = Bird(
        internal_id=record.internal_id,
        ring_number=record.ring_number,
        tag_id=record.tag_id,
        animal_class=record.animal_class,
        species=record.species,
        gender=record.gender,
        estimated_age=record.estimated_age,
        found_location=record.found_location,
        finder_name=record.finder_name,
        finder_contact=record.finder_contact,
        gps_lat=record.gps_lat,
        gps_lon=record.gps_lon,
        station_id=record.station_id,
        notes=record.notes,
        admission_date=datetime.utcnow(),
        status=BirdStatus.IN_TREATMENT,
    )
    db.add(new_bird)
    db.commit()
    db.refresh(new_bird)
    return new_bird


def _update_patient_record(patient_id: int, update: BirdUpdate, db):
    bird = db.query(Bird).filter(Bird.id == patient_id).first()
    if not bird:
        return None

    if update.status is not None:
        bird.status = update.status
    if update.enclosure_id is not None:
        bird.enclosure_id = update.enclosure_id
    if update.estimated_age is not None:
        bird.estimated_age = update.estimated_age
    if update.notes is not None:
        bird.notes = update.notes
    if update.release_date is not None:
        bird.release_date = update.release_date

    bird.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(bird)
    return bird

@app.post("/birds", response_model=BirdSchema, tags=["Patients"])
async def create_bird(
    bird: BirdCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create new patient record"""
##    user = verify_token(token)
##    if not user:
##        raise HTTPException(status_code=401, detail="Invalid credentials")
##    return _create_patient_record(bird, db)

"""Temporär alle freigeschaltet"""
def verify_token(token: str):
    return {"user": "dev"}

@app.post("/patients", response_model=BirdSchema, tags=["Patients"])
async def create_patient(
    patient: PatientCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create new patient record under generic patient endpoint."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _create_patient_record(patient, db)

@app.patch("/birds/{bird_id}", response_model=BirdSchema, tags=["Patients"])
async def update_bird(
    bird_id: int,
    bird_update: BirdUpdate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Update patient record."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    bird = _update_patient_record(bird_id, bird_update, db)
    if not bird:
        raise HTTPException(status_code=404, detail="Bird not found")
    return bird

@app.patch("/patients/{patient_id}", response_model=BirdSchema, tags=["Patients"])
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Update patient record through the generic endpoint."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    bird = _update_patient_record(patient_id, patient_update, db)
    if not bird:
        raise HTTPException(status_code=404, detail="Patient not found")
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

    bird = db.query(Bird).filter(Bird.id == bird_id).first()
    if not bird:
        raise HTTPException(status_code=404, detail="Bird not found")
    return bird

@app.get("/patients/{patient_id}", response_model=BirdSchema, tags=["Patients"])
async def get_patient(
    patient_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Get patient details through the generic endpoint."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    bird = db.query(Bird).filter(Bird.id == patient_id).first()
    if not bird:
        raise HTTPException(status_code=404, detail="Patient not found")
    return bird

@app.get("/birds", tags=["Patients"])
async def list_birds(
    skip: int = 0,
    limit: int = 100,
    station_id: Optional[str] = None,
    animal_class: Optional[AnimalClass] = None,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List all patients, optionally filtered by station or animal class."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    query = db.query(Bird)
    if station_id:
        query = query.filter(Bird.station_id == station_id)
    if animal_class:
        query = query.filter(Bird.animal_class == animal_class)

    total = query.count()
    birds = query.offset(skip).limit(limit).all()
    return {"patients": birds, "total": total}

@app.get("/patients", tags=["Patients"])
async def list_patients(
    skip: int = 0,
    limit: int = 100,
    station_id: Optional[str] = None,
    animal_class: Optional[AnimalClass] = None,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List all patients, optionally filtered by station or animal class."""
    return await list_birds(skip, limit, station_id, animal_class, token, db)

@app.post("/sync", tags=["Sync"])
async def sync_station(
    payload: dict,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Sync offline station actions with the server."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    station_id = payload.get("station_id")
    actions = payload.get("actions", [])

    if not station_id:
        raise HTTPException(status_code=400, detail="station_id is required")

    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        station = Station(
            station_id=station_id,
            name=f"Station {station_id}",
            location="Unknown"
        )
        db.add(station)
        db.commit()

    sync_manager = SyncManager(db)
    processed_count = 0
    errors = []

    for action in actions:
        action_type = action.get("action")
        entity_type = action.get("entity_type")
        entity_data = action.get("data", {})

        if not action_type or not entity_type:
            errors.append({"action": action, "error": "Missing action or entity_type"})
            continue

        if action_type == "create" and entity_type in ("bird", "patient", "animal"):
            try:
                bird = Bird(
                    internal_id=entity_data.get("internal_id", f"unknown-{datetime.utcnow().timestamp()}"),
                    ring_number=entity_data.get("ring_number"),
                    tag_id=entity_data.get("tag_id"),
                    animal_class=entity_data.get("animal_class", "bird"),
                    species=entity_data.get("species", "other"),
                    gender=entity_data.get("gender", "unknown"),
                    estimated_age=entity_data.get("estimated_age"),
                    found_location=entity_data.get("found_location"),
                    finder_name=entity_data.get("finder_name"),
                    finder_contact=entity_data.get("finder_contact"),
                    gps_lat=entity_data.get("gps_lat"),
                    gps_lon=entity_data.get("gps_lon"),
                    station_id=station_id,
                    notes=entity_data.get("notes"),
                    admission_date=datetime.utcnow(),
                    status=BirdStatus.IN_TREATMENT,
                )
                db.add(bird)
                db.commit()
                processed_count += 1
            except Exception as exc:
                db.rollback()
                errors.append({"action": action, "error": str(exc)})

        elif action_type == "create" and entity_type == "calendar_event":
            try:
                event = CalendarEvent(
                    title=entity_data.get("title", "Untitled event"),
                    station_id=station_id,
                    bird_id=entity_data.get("bird_id"),
                    description=entity_data.get("description"),
                    start_at=datetime.fromisoformat(entity_data.get("start_at")) if entity_data.get("start_at") else datetime.utcnow(),
                    end_at=datetime.fromisoformat(entity_data.get("end_at")) if entity_data.get("end_at") else None,
                    all_day=entity_data.get("all_day", False),
                    location=entity_data.get("location"),
                )
                db.add(event)
                db.commit()
                processed_count += 1
            except Exception as exc:
                db.rollback()
                errors.append({"action": action, "error": str(exc)})

        elif action_type == "create" and entity_type == "health_record":
            try:
                bird_id = entity_data.get("bird_id")
                health_record = HealthRecord(
                    bird_id=bird_id,
                    weight_grams=entity_data.get("weight_grams"),
                    general_condition=entity_data.get("general_condition"),
                    behavior=entity_data.get("behavior"),
                    hydration_status=entity_data.get("hydration_status"),
                    injuries=entity_data.get("injuries"),
                    medical_notes=entity_data.get("medical_notes"),
                    parasites_detected=entity_data.get("parasites_detected", False),
                    parasite_notes=entity_data.get("parasite_notes"),
                    fecal_sample_taken=entity_data.get("fecal_sample_taken", False),
                    lab_results=entity_data.get("lab_results"),
                    recorded_at=datetime.fromisoformat(entity_data.get("recorded_at")) if entity_data.get("recorded_at") else datetime.utcnow(),
                )
                db.add(health_record)
                db.commit()
                processed_count += 1
            except Exception as exc:
                db.rollback()
                errors.append({"action": action, "error": str(exc)})

        else:
            sync_success = sync_manager.enqueue_action(
                station_id=station_id,
                action=action_type,
                entity_type=entity_type,
                entity_data=entity_data,
            )
            if sync_success:
                processed_count += 1
            else:
                errors.append({"action": action, "error": "Failed to enqueue action"})

    return {
        "success": len(errors) == 0,
        "processed": processed_count,
        "errors": errors,
    }

@app.get("/stations", tags=["Stations"])
async def list_stations(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List all registered stations and sync queue status."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stations = db.query(Station).all()
    sync_manager = SyncManager(db)
    station_list = []

    for station in stations:
        stats = sync_manager.get_queue_stats(station.station_id)
        station_list.append({
            "station_id": station.station_id,
            "name": station.name,
            "location": station.location,
            "gps_lat": station.gps_lat,
            "gps_lon": station.gps_lon,
            "contact_email": station.contact_email,
            "contact_phone": station.contact_phone,
            "staff": station.staff or [],
            "created_at": station.created_at.isoformat(),
            "updated_at": station.updated_at.isoformat(),
            "sync_stats": stats,
        })

    return {"stations": station_list}

@app.get("/stations/{station_id}", response_model=StationSchema, tags=["Stations"])
async def get_station(
    station_id: str,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Get station metadata and staff details."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    return station

@app.patch("/stations/{station_id}", response_model=StationSchema, tags=["Stations"])
async def update_station(
    station_id: str,
    station_update: StationUpdate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Update station metadata, name, contact details, and staff."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    station = db.query(Station).filter(Station.station_id == station_id).first()
    if not station:
        raise HTTPException(status_code=404, detail="Station not found")

    if station_update.name is not None:
        station.name = station_update.name
    if station_update.location is not None:
        station.location = station_update.location
    if station_update.gps_lat is not None:
        station.gps_lat = station_update.gps_lat
    if station_update.gps_lon is not None:
        station.gps_lon = station_update.gps_lon
    if station_update.contact_email is not None:
        station.contact_email = station_update.contact_email
    if station_update.contact_phone is not None:
        station.contact_phone = station_update.contact_phone
    if station_update.staff is not None:
        station.staff = [member.dict() for member in station_update.staff]

    station.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(station)
    return station

# ============================================================================
# REPORTS & FILE UPLOAD
# ============================================================================

@app.get("/reports/overview", tags=["Reports"])
async def get_overview_report(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Return high-level counts for dashboard reporting."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    total_patients = db.query(Bird).count()
    total_stations = db.query(Station).count()
    total_events = db.query(CalendarEvent).count()
    total_media = db.query(Media).count()
    total_ready_for_release = db.query(Bird).filter(Bird.status == BirdStatus.READY_FOR_RELEASE).count()
    total_deceased = db.query(Bird).filter(Bird.status == BirdStatus.DECEASED).count()

    animal_counts = {
        "bird": db.query(Bird).filter(Bird.animal_class == "bird").count(),
        "reptile": db.query(Bird).filter(Bird.animal_class == "reptile").count(),
        "mammal": db.query(Bird).filter(Bird.animal_class == "mammal").count(),
        "other": db.query(Bird).filter(Bird.animal_class == "other").count(),
    }

    return {
        "total_birds": total_patients,
        "total_patients": total_patients,
        "total_stations": total_stations,
        "total_calendar_events": total_events,
        "total_media_files": total_media,
        "total_ready_for_release": total_ready_for_release,
        "total_deceased": total_deceased,
        "animal_class_counts": animal_counts,
    }

@app.get("/reports/alerts", tags=["Reports"])
async def get_report_alerts(
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Return alert counts for care and release readiness."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    ready_count = db.query(Bird).filter(Bird.status == BirdStatus.READY_FOR_RELEASE).count()
    deceased_count = db.query(Bird).filter(Bird.status == BirdStatus.DECEASED).count()
    in_treatment_count = db.query(Bird).filter(Bird.status == BirdStatus.IN_TREATMENT).count()

    return {
        "ready_for_release": ready_count,
        "deceased": deceased_count,
        "in_treatment": in_treatment_count,
        "animal_class_counts": {
            "bird": db.query(Bird).filter(Bird.animal_class == "bird").count(),
            "reptile": db.query(Bird).filter(Bird.animal_class == "reptile").count(),
            "mammal": db.query(Bird).filter(Bird.animal_class == "mammal").count(),
            "other": db.query(Bird).filter(Bird.animal_class == "other").count(),
        },
    }

@app.post("/birds/{bird_id}/media", response_model=MediaSchema, tags=["Media"])
async def upload_bird_media(
    bird_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Upload a media file for a patient record."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    bird = db.query(Bird).filter(Bird.id == bird_id).first()
    if not bird:
        raise HTTPException(status_code=404, detail="Bird not found")

    upload_path = Path(settings.UPLOAD_DIR)
    upload_path.mkdir(parents=True, exist_ok=True)
    timestamp = int(time.time())
    dest_name = f"bird_{bird_id}_{timestamp}_{file.filename.replace(' ', '_')}"
    dest_file = upload_path / dest_name

    with dest_file.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    media = Media(
        bird_id=bird_id,
        file_path=str(dest_file),
        file_name=file.filename,
        file_type=file.content_type,
        file_size_bytes=dest_file.stat().st_size,
        description=description,
    )
    db.add(media)
    db.commit()
    db.refresh(media)
    return media

@app.get("/birds/{bird_id}/media", response_model=List[MediaSchema], tags=["Media"])
async def list_bird_media(
    bird_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List uploaded media files for a patient."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    medias = db.query(Media).filter(Media.bird_id == bird_id).all()
    return medias

@app.post("/patients/{patient_id}/media", response_model=MediaSchema, tags=["Media"])
async def upload_patient_media(
    patient_id: int,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Upload a media file for a patient record through the generic endpoint."""
    return await upload_bird_media(patient_id, file, description, token, db)

@app.get("/patients/{patient_id}/media", response_model=List[MediaSchema], tags=["Media"])
async def list_patient_media(
    patient_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List uploaded media files for a patient."""
    return await list_bird_media(patient_id, token, db)

@app.post("/patients/{patient_id}/health-records", response_model=HealthRecordSchema, tags=["Health"])
async def create_patient_health_record(
    patient_id: int,
    record_data: HealthRecordCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create daily health check record for a patient."""
    return await create_health_record(patient_id, record_data, token, db)

@app.post("/patients/{patient_id}/feeding-logs", response_model=FeedingLogSchema, tags=["Feeding"])
async def create_patient_feeding_log(
    patient_id: int,
    log_data: FeedingLogCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create feeding log entry for a patient."""
    return await create_feeding_log(patient_id, log_data, token, db)

# ============================================================================
# CALENDAR ENDPOINTS
# ============================================================================

@app.get("/calendar/events", response_model=List[CalendarEventSchema], tags=["Calendar"])
async def list_calendar_events(
    station_id: str,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """List calendar events for a station."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    events = db.query(CalendarEvent).filter(CalendarEvent.station_id == station_id).order_by(CalendarEvent.start_at).all()
    return events

@app.post("/calendar/events", response_model=CalendarEventSchema, tags=["Calendar"])
async def create_calendar_event(
    event_data: CalendarEventCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create or sync a calendar event."""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    event = CalendarEvent(
        title=event_data.title,
        station_id=event_data.station_id,
        bird_id=event_data.bird_id,
        description=event_data.description,
        start_at=event_data.start_at,
        end_at=event_data.end_at,
        all_day=event_data.all_day,
        location=event_data.location,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event

# ============================================================================
# HEALTH RECORD ENDPOINTS
# ============================================================================

@app.post("/birds/{bird_id}/health-records", response_model=HealthRecordSchema, tags=["Health"])
async def create_health_record(
    bird_id: int,
    record_data: HealthRecordCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create daily health check record"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    bird = db.query(Bird).filter(Bird.id == bird_id).first()
    if not bird:
        raise HTTPException(status_code=404, detail="Bird not found")

    health_record = HealthRecord(
        bird_id=bird_id,
        weight_grams=record_data.weight_grams,
        general_condition=record_data.general_condition,
        behavior=record_data.behavior,
        hydration_status=record_data.hydration_status,
        injuries=record_data.injuries,
        medical_notes=record_data.medical_notes,
        parasites_detected=record_data.parasites_detected,
        parasite_notes=record_data.parasite_notes,
        fecal_sample_taken=record_data.fecal_sample_taken,
        lab_results=record_data.lab_results,
        recorded_at=datetime.utcnow(),
    )

    db.add(health_record)
    db.commit()
    db.refresh(health_record)

    return health_record

# ============================================================================
# FEEDING LOG ENDPOINTS
# ============================================================================

@app.post("/birds/{bird_id}/feeding-logs", response_model=FeedingLogSchema, tags=["Feeding"])
async def create_feeding_log(
    bird_id: int,
    log_data: FeedingLogCreate,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Create feeding log entry"""
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    bird = db.query(Bird).filter(Bird.id == bird_id).first()
    if not bird:
        raise HTTPException(status_code=404, detail="Bird not found")

    feeding_log = FeedingLog(
        bird_id=bird_id,
        feed_type=log_data.feed_type,
        amount_grams=log_data.amount_grams,
        time_of_day=log_data.time_of_day,
        food_consumed=log_data.food_consumed,
        feeding_method=log_data.feeding_method,
        notes=log_data.notes,
    )

    db.add(feeding_log)
    db.commit()
    db.refresh(feeding_log)

    return feeding_log

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

    bird = db.query(Bird).filter(Bird.id == bird_id).first()
    if not bird:
        raise HTTPException(status_code=404, detail="Bird not found")

    health_records = db.query(HealthRecord).filter(HealthRecord.bird_id == bird_id).order_by(HealthRecord.recorded_at.desc()).all()
    health_history = [
        {
            "recorded_at": record.recorded_at.isoformat(),
            "weight_grams": record.weight_grams,
            "behavior": record.behavior,
            "hydration_status": record.hydration_status,
            "injuries": record.injuries,
            "medical_notes": record.medical_notes,
        }
        for record in health_records
    ]

    bird_data = {
        "species": bird.species.value if hasattr(bird.species, "value") else bird.species,
        "status": bird.status.value if hasattr(bird.status, "value") else bird.status,
        "estimated_age": bird.estimated_age,
        "gender": bird.gender.value if hasattr(bird.gender, "value") else bird.gender,
        "gps_lat": bird.gps_lat,
        "gps_lon": bird.gps_lon,
        "notes": bird.notes,
        "station_id": bird.station_id,
    }

    recommendations = ai.generate_care_recommendations(bird_data, health_history)
    return {"recommendations": recommendations}

@app.post("/patients/{patient_id}/recommendations", tags=["AI"])
async def get_patient_recommendations(
    patient_id: int,
    token: str = Depends(oauth2_scheme),
    db = Depends(get_db)
):
    """Get LLM-based care recommendations for a patient."""
    return await get_ai_recommendations(patient_id, token, db)

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

@app.get("/ui/{full_path:path}")
async def ui_spa_fallback(full_path: str):
    return FileResponse("server/static_ui/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
    )

