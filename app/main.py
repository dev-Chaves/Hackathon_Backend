from fastapi import FastAPI

from app.core.config import settings
from app.modules.motor1.router import router as motor1_router
from app.modules.motor2.router import router as motor2_router
from app.modules.motor3.router import router as motor3_router

app = FastAPI(
    title=settings.app_name,
    debug=settings.app_debug,
    version="0.1.0",
)


@app.get("/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(motor1_router, prefix="/api/v1/motor1")
app.include_router(motor2_router, prefix="/api/v1/motor2")
app.include_router(motor3_router, prefix="/api/v1/motor3")

