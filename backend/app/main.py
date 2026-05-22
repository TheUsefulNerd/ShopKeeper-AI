"""
FastAPI application entry point.

Run with: uvicorn app.main:app --reload
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import auth as auth_router
from config import settings

app = FastAPI(
    title="ShopKeeper AI",
    version="1.0.0",
    description="Retro pixel-art game with a real multi-agent AI backend.",
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router.router, prefix="/api/v1")
