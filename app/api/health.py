"""Health check endpoint."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health():
    """Health check — returns status ok."""
    return {"status": "ok"}
