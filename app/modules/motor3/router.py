from fastapi import APIRouter

router = APIRouter(tags=["motor3 - capacitacao"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"motor": "motor3", "status": "ready"}

