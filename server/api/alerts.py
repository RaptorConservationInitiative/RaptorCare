from fastapi import APIRouter
from server.state import EVENTS

router = APIRouter()

@router.get("/alerts")
def alerts():

    deaths = [
        e for e in EVENTS
        if e.get("type") == "mortality"
    ]

    if len(deaths) > 3:
        return {
            "alert": "MORTALITY_CLUSTER",
            "count": len(deaths)
        }

    return {"alert": None}