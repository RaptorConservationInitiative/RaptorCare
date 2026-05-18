from fastapi import FastAPI
from server.api import events, ai, alerts, export

app = FastAPI(title="RaptorCare Enterprise")

app.include_router(events.router)
app.include_router(ai.router)
app.include_router(alerts.router)
app.include_router(export.router)

@app.get("/health")
def health():
    return {"status": "ok"}