from fastapi import APIRouter
from server.state import EVENTS

router = APIRouter()

@router.get("/export")
def export_data():

    return {
        "events": len(EVENTS),
        "format": "research_ready"
    }