from fastapi import APIRouter
from server.state import EVENTS
from server.core.audit import append_audit

router = APIRouter()

@router.post("/event")
def ingest_event(event: dict):

    EVENTS.append(event)
    append_audit(event)

    return {
        "status": "stored",
        "count": len(EVENTS)
    }

@router.get("/events")
def get_events():
    return EVENTS