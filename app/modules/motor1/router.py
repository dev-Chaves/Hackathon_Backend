from fastapi import APIRouter

router = APIRouter(tags=["motor1 - risco e cobertura"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"motor": "motor1", "status": "ready"}

