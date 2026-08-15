from fastapi import APIRouter

router = APIRouter(tags=["motor2 - matchmaking"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"motor": "motor2", "status": "ready"}

