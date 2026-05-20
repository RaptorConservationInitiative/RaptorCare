"""
Pydantic schemas for API request/response validation
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum

# ============================================================================
# ENUMS
# ============================================================================

class BirdStatusSchema(str, Enum):
    IN_TREATMENT = "in_treatment"
    READY_FOR_RELEASE = "ready_for_release"
    PERMANENTLY_NON_RELEASABLE = "permanently_non_releasable"
    DECEASED = "deceased"

class AnimalClassSchema(str, Enum):
    BIRD = "bird"
    REPTILE = "reptile"
    MAMMAL = "mammal"
    OTHER = "other"

class SpeciesTypeSchema(str, Enum):
    PEREGRINE_FALCON = "peregrine_falcon"
    EURASIAN_EAGLE_OWL = "eurasian_eagle_owl"
    RED_KITE = "red_kite"
    COMMON_KESTREL = "common_kestrel"
    COMMON_BUZZARD = "common_buzzard"
    EURASIAN_SPARROWHAWK = "eurasian_sparrowhawk"
    GREEN_IGUANA = "green_iguana"
    BALL_PYTHON = "ball_python"
    RED_FOX = "red_fox"
    EUROPEAN_HEDGEHOG = "european_hedgehog"
    COMMON_WALLABY = "common_wallaby"
    OTHER = "other"

class GenderSchema(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class UserRoleSchema(str, Enum):
    ADMIN = "admin"
    CARETAKER = "caretaker"
    VETERINARIAN = "veterinarian"
    RESEARCHER = "researcher"

# ============================================================================
# AUTH SCHEMAS
# ============================================================================

class TokenResponse(BaseModel):
    """OAuth2 token response"""
    access_token: str
    token_type: str = "bearer"

class ResearchPrompt(BaseModel):
    """Payload for research and analysis requests"""
    bird_data: Optional[Dict[str, Any]] = None
    health_history: Optional[List[Dict[str, Any]]] = None
    notes: Optional[str] = None
    research_goal: Optional[str] = None

class ResearchOutput(BaseModel):
    """Response for research and LLM analysis endpoints"""
    research_text: str
    gpu_used: Optional[int] = None
    model: Optional[str] = None

class GPUInfoSchema(BaseModel):
    device_id: int
    name: str
    total_memory_gb: float
    used_memory_gb: float
    free_memory_gb: float
    utilization_percent: float

class GPUStatusResponse(BaseModel):
    gpu_count: int
    gpus: List[GPUInfoSchema]

class UserCreate(BaseModel):
    """User creation request"""
    username: str = Field(..., min_length=3, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: UserRoleSchema = UserRoleSchema.CARETAKER

class UserSchema(BaseModel):
    """User response"""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRoleSchema
    is_active: bool
    created_at: datetime

# ============================================================================
# BIRD (PATIENT) SCHEMAS
# ============================================================================

class BirdCreate(BaseModel):
    """Bird creation request"""
    internal_id: str
    ring_number: Optional[str] = None
    tag_id: Optional[str] = None
    animal_class: AnimalClassSchema = AnimalClassSchema.BIRD
    species: SpeciesTypeSchema
    gender: GenderSchema = GenderSchema.UNKNOWN
    estimated_age: Optional[str] = None
    found_location: Optional[str] = None
    finder_name: Optional[str] = None
    finder_contact: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_lon: Optional[float] = None
    station_id: str
    notes: Optional[str] = None

class BirdUpdate(BaseModel):
    """Bird update request"""
    status: Optional[BirdStatusSchema] = None
    enclosure_id: Optional[str] = None
    estimated_age: Optional[str] = None
    notes: Optional[str] = None
    release_date: Optional[datetime] = None

class BirdSchema(BirdCreate):
    """Bird response"""
    id: int
    status: BirdStatusSchema
    admission_date: datetime
    release_date: Optional[datetime]
    enclosure_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ============================================================================
# HEALTH RECORD SCHEMAS
# ============================================================================

class HealthRecordCreate(BaseModel):
    """Health record creation request"""
    weight_grams: Optional[float] = None
    general_condition: Optional[str] = None
    behavior: Optional[str] = None
    hydration_status: Optional[str] = None
    injuries: Optional[str] = None
    medical_notes: Optional[str] = None
    parasites_detected: bool = False
    parasite_notes: Optional[str] = None
    fecal_sample_taken: bool = False
    lab_results: Optional[str] = None

class HealthRecordSchema(HealthRecordCreate):
    """Health record response"""
    id: int
    bird_id: int
    recorded_at: datetime
    created_at: datetime

    class Config:
        orm_mode = True

# ============================================================================
# MEDICATION SCHEMAS
# ============================================================================

class MedicationCreate(BaseModel):
    """Medication prescription creation"""
    drug_name: str
    dosage: str
    frequency: Optional[str] = None
    route: Optional[str] = None
    start_date: datetime
    end_date: Optional[datetime] = None
    indication: Optional[str] = None

class MedicationSchema(MedicationCreate):
    """Medication response"""
    id: int
    bird_id: int
    created_at: datetime

class MedicationDoseCreate(BaseModel):
    """Medication dose administration"""
    medication_id: int
    administered_at: datetime
    notes: Optional[str] = None

# ============================================================================
# FEEDING LOG SCHEMAS
# ============================================================================

class FeedingLogCreate(BaseModel):
    """Feeding log creation request"""
    feed_type: str
    amount_grams: Optional[float] = None
    time_of_day: str
    food_consumed: Optional[bool] = None
    feeding_method: str = "self"  # "self", "assist", "force"
    notes: Optional[str] = None

class FeedingLogSchema(FeedingLogCreate):
    """Feeding log response"""
    id: int
    bird_id: int
    recorded_at: datetime
    created_at: datetime

    class Config:
        orm_mode = True

# ============================================================================
# MEDIA SCHEMAS
# ============================================================================

class MediaSchema(BaseModel):
    """Media/file attachment"""
    id: int
    bird_id: int
    file_name: str
    file_type: Optional[str]
    file_size_bytes: Optional[int]
    description: Optional[str]
    uploaded_at: datetime

# ============================================================================
# TIMELINE EVENT SCHEMAS
# ============================================================================

class TimelineEventCreate(BaseModel):
    """Timeline event creation"""
    event_type: str  # "admission", "surgery", "release", "death", etc.
    event_date: datetime
    title: Optional[str] = None
    description: Optional[str] = None

class TimelineEventSchema(TimelineEventCreate):
    """Timeline event response"""
    id: int
    bird_id: int
    created_at: datetime

# ============================================================================
# CALENDAR EVENT SCHEMAS
# ============================================================================

class CalendarEventCreate(BaseModel):
    """Calendar event creation request"""
    title: str
    station_id: str
    start_at: datetime
    end_at: Optional[datetime] = None
    all_day: bool = False
    description: Optional[str] = None
    location: Optional[str] = None
    bird_id: Optional[int] = None

class CalendarEventSchema(CalendarEventCreate):
    """Calendar event response"""
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# ============================================================================
# AI/RECOMMENDATION SCHEMAS
# ============================================================================

class AIRecommendationRequest(BaseModel):
    """Request AI recommendations for a bird"""
    bird_id: int
    context: Optional[str] = None

class AIRecommendationResponse(BaseModel):
    """AI recommendation response"""
    bird_id: int
    recommendations: List[str]
    prognosis: str
    confidence: float = 0.0
    generated_at: datetime

# ============================================================================
# SYNC SCHEMAS
# ============================================================================

class SyncPayload(BaseModel):
    """Offline sync payload from station client"""
    station_id: str
    actions: List[dict]  # Each action: {"type": "create", "entity": "bird", "data": {...}}
    timestamp: datetime
    device_id: Optional[str] = None

class SyncResponse(BaseModel):
    """Response to sync request"""
    success: bool
    synced_count: int
    errors: List[str] = []
    server_data: Optional[dict] = None
