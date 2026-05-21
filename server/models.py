"""
SQLAlchemy ORM models for RaptorCare
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
import enum

from server.database import Base
from server.auth import get_password_hash

# ============================================================================
# ENUMS
# ============================================================================

class BirdStatus(str, enum.Enum):
    """Bird rehabilitation status"""
    IN_TREATMENT = "in_treatment"
    READY_FOR_RELEASE = "ready_for_release"
    PERMANENTLY_NON_RELEASABLE = "permanently_non_releasable"
    DECEASED = "deceased"

class AnimalClass(str, enum.Enum):
    """High-level animal categories"""
    BIRD = "bird"
    REPTILE = "reptile"
    MAMMAL = "mammal"
    OTHER = "other"

class SpeciesType(str, enum.Enum):
    """Patient species types across birds, reptiles and mammals"""
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

class Gender(str, enum.Enum):
    """Bird gender"""
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class UserRole(str, enum.Enum):
    """User roles and permissions"""
    ADMIN = "admin"
    CARETAKER = "caretaker"
    VETERINARIAN = "veterinarian"
    RESEARCHER = "researcher"

# ============================================================================
# USER MANAGEMENT
# ============================================================================

class User(Base):
    """System user accounts"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(UserRole), default=UserRole.CARETAKER)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_records = relationship("HealthRecord", back_populates="recorded_by")
    feeding_logs = relationship("FeedingLog", back_populates="recorded_by")
    audit_logs = relationship("AuditLog", back_populates="user")

    def set_password(self, password: str):
        """Hash and set password"""
        self.hashed_password = get_password_hash(password)

# ============================================================================
# BIRD (PATIENT) MANAGEMENT
# ============================================================================

class Bird(Base):
    """Raptor patient records"""
    __tablename__ = "birds"

    # Identification
    id = Column(Integer, primary_key=True, index=True)
    internal_id = Column(String(50), unique=True, index=True)
    ring_number = Column(String(50), unique=True, nullable=True)
    tag_id = Column(String(50), unique=True, nullable=True)

    # Species information
    animal_class = Column(Enum(AnimalClass), default=AnimalClass.BIRD)
    species = Column(Enum(SpeciesType), nullable=False)
    gender = Column(Enum(Gender), default=Gender.UNKNOWN)
    estimated_age = Column(String(50))  # e.g., "juvenile", "2 years", "adult"

    # Location & rescue info
    found_location = Column(String(255))
    finder_name = Column(String(255))
    finder_contact = Column(String(255))
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)

    # Status tracking
    admission_date = Column(DateTime, nullable=False)
    status = Column(Enum(BirdStatus), default=BirdStatus.IN_TREATMENT)
    release_date = Column(DateTime, nullable=True)
    station_id = Column(String(50), nullable=False)  # Multi-station support
    enclosure_id = Column(String(50), nullable=True)  # Current housing

    # General notes
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_records = relationship("HealthRecord", back_populates="bird", cascade="all, delete-orphan")
    feeding_logs = relationship("FeedingLog", back_populates="bird", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="bird", cascade="all, delete-orphan")
    media = relationship("Media", back_populates="bird", cascade="all, delete-orphan")
    events = relationship("TimelineEvent", back_populates="bird", cascade="all, delete-orphan")
    calendar_events = relationship("CalendarEvent", back_populates="bird", cascade="all, delete-orphan")

# ============================================================================
# HEALTH & MEDICAL DATA
# ============================================================================

class HealthRecord(Base):
    """Daily health check entries"""
    __tablename__ = "health_records"

    id = Column(Integer, primary_key=True, index=True)
    bird_id = Column(Integer, ForeignKey("birds.id"), nullable=False)
    recorded_by_id = Column(Integer, ForeignKey("users.id"))

    # Daily observations
    weight_grams = Column(Float, nullable=True)
    general_condition = Column(String(255))  # e.g., "good", "fair", "critical"
    behavior = Column(Text)
    hydration_status = Column(String(100))  # e.g., "well-hydrated", "dehydrated"

    # Injury/illness documentation
    injuries = Column(Text)
    medical_notes = Column(Text)
    parasites_detected = Column(Boolean, default=False)
    parasite_notes = Column(Text)

    # Laboratory
    fecal_sample_taken = Column(Boolean, default=False)
    lab_results = Column(Text)

    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bird = relationship("Bird", back_populates="health_records")
    recorded_by = relationship("User", back_populates="health_records")
    medications_given = relationship("MedicationDose", back_populates="health_record")

class Medication(Base):
    """Medication prescriptions"""
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    bird_id = Column(Integer, ForeignKey("birds.id"), nullable=False)

    drug_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100))  # e.g., "2x daily", "once every 12h"
    route = Column(String(50))  # e.g., "oral", "injection", "topical"
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=True)
    indication = Column(Text)  # Why prescribed

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bird = relationship("Bird", back_populates="medications")
    doses = relationship("MedicationDose", back_populates="medication")

class MedicationDose(Base):
    """Actual medication administration records"""
    __tablename__ = "medication_doses"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    health_record_id = Column(Integer, ForeignKey("health_records.id"))

    administered_at = Column(DateTime, nullable=False)
    notes = Column(Text)

    # Relationships
    medication = relationship("Medication", back_populates="doses")
    health_record = relationship("HealthRecord", back_populates="medications_given")

# ============================================================================
# FEEDING & NUTRITION
# ============================================================================

class FeedingLog(Base):
    """Feeding protocol entries"""
    __tablename__ = "feeding_logs"

    id = Column(Integer, primary_key=True, index=True)
    bird_id = Column(Integer, ForeignKey("birds.id"), nullable=False)
    recorded_by_id = Column(Integer, ForeignKey("users.id"))

    feed_type = Column(String(100), nullable=False)  # e.g., "chick", "quail", "mouse"
    amount_grams = Column(Float)
    time_of_day = Column(String(20))  # e.g., "08:00", "14:00", "20:00"
    food_consumed = Column(Boolean, nullable=True)  # Did bird eat?
    feeding_method = Column(String(50))  # "self", "assist", "force"

    notes = Column(Text)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bird = relationship("Bird", back_populates="feeding_logs")
    recorded_by = relationship("User", back_populates="feeding_logs")

# ============================================================================
# MEDIA & DOCUMENTATION
# ============================================================================

class Media(Base):
    """File attachments (photos, X-rays, reports)"""
    __tablename__ = "media"

    id = Column(Integer, primary_key=True, index=True)
    bird_id = Column(Integer, ForeignKey("birds.id"), nullable=False)

    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(50))  # e.g., "image/jpeg", "application/pdf"
    file_size_bytes = Column(Integer)
    description = Column(Text)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bird = relationship("Bird", back_populates="media")

# ============================================================================
# TIMELINE & EVENTS
# ============================================================================

class TimelineEvent(Base):
    """Chronological log of significant events"""
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, index=True)
    bird_id = Column(Integer, ForeignKey("birds.id"), nullable=False)

    event_type = Column(String(50), nullable=False)  # e.g., "admission", "surgery", "release", "death"
    event_date = Column(DateTime, nullable=False)
    title = Column(String(255))
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    bird = relationship("Bird", back_populates="events")

class CalendarEvent(Base):
    """Scheduled care, release and procedure events"""
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)
    bird_id = Column(Integer, ForeignKey("birds.id"), nullable=True)
    station_id = Column(String(50), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text)
    start_at = Column(DateTime, nullable=False)
    end_at = Column(DateTime, nullable=True)
    all_day = Column(Boolean, default=False)
    location = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    bird = relationship("Bird", back_populates="calendar_events")

# ============================================================================
# STATION & ENCLOSURE MANAGEMENT
# ============================================================================

class Station(Base):
    """Rescue station locations"""
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String(50), unique=True, index=True)
    name = Column(String(255), nullable=False)
    location = Column(String(255))
    gps_lat = Column(Float, nullable=True)
    gps_lon = Column(Float, nullable=True)
    contact_email = Column(String(255))
    contact_phone = Column(String(20))
    staff = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Enclosure(Base):
    """Aviaries and enclosures"""
    __tablename__ = "enclosures"

    id = Column(Integer, primary_key=True, index=True)
    enclosure_id = Column(String(50), unique=True, index=True)
    station_id = Column(String(50), ForeignKey("stations.station_id"))
    name = Column(String(255))
    enclosure_type = Column(String(100))  # e.g., "isolation", "recovery", "flight"
    capacity = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

# ============================================================================
# AUDIT & SYNC
# ============================================================================

class AuditLog(Base):
    """System audit trail"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255), nullable=False)
    entity_type = Column(String(50))  # e.g., "bird", "health_record"
    entity_id = Column(Integer)
    changes = Column(Text)  # JSON of what changed

    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

class SyncQueue(Base):
    """Offline sync queue for station clients"""
    __tablename__ = "sync_queue"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(String(50), nullable=False)
    action = Column(String(20))  # "create", "update", "delete"
    entity_type = Column(String(50))
    entity_data = Column(Text)  # JSON payload

    queued_at = Column(DateTime, default=datetime.utcnow)
    synced_at = Column(DateTime, nullable=True)
    sync_status = Column(String(20), default="pending")  # "pending", "completed", "failed"
