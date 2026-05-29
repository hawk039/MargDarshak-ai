"""Health check endpoint."""

from fastapi import APIRouter

health_router = APIRouter(tags=["Health"])


@health_router.get("/health", summary="Service health check")
async def health_check() -> dict[str, str]:
    """Return a simple health response."""

    return {"status": "ok", "service": "marg-darshak-ai-service"}
