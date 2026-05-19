from fastapi import FastAPI
from server.api import animals, stations, events, health, sync

app = FastAPI(title="RaptorCare Core")

app.include_router(animals.router)
app.include_router(stations.router)
app.include_router(events.router)
app.include_router(health.router)
app.include_router(sync.router)
