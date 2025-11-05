"""Health check endpoint router"""
from fastapi import APIRouter
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint

    Returns:
        Health status of the service
    """
    return HealthResponse(
        status="healthy",
        service="ChromaticBotBackEnd"
    )
