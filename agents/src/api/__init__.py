"""API routes."""
from fastapi import APIRouter
from .routes_webhooks import router as webhooks_router
from .routes_analysis import router as analysis_router
from .routes_proposals import router as proposals_router

api_router = APIRouter()
api_router.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(proposals_router, prefix="/proposals", tags=["Proposals & Approval"])

__all__ = ["api_router"]
