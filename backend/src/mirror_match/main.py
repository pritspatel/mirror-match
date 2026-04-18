"""FastAPI app entry point."""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from . import __version__
from .api.auth import auth_middleware
from .api.metrics import metrics_middleware
from .api.metrics import router as metrics_router
from .api.routes_compare import router as compare_router

app = FastAPI(
    title="MirrorMatch",
    version=__version__,
    description="Field-level JSON comparison tool",
)

_cors_origins = os.environ.get(
    "MIRROR_MATCH_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(BaseHTTPMiddleware, dispatch=metrics_middleware)
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _cors_origins if o.strip()],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(compare_router)
app.include_router(metrics_router)


@app.get("/api/v1/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "version": __version__}
