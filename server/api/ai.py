from fastapi import APIRouter
from server.ml.inference import predict_release

router = APIRouter()

@router.post("/ai/release")
def release(data: dict):
    return predict_release(data)