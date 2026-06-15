"""FastAPI application entrypoint."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import config
from database import init_db
from providers import get_provider
from routes import annotations, filters, images, search


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Fashion Inspiration Library",
    description="AI-powered garment classification, search, and annotation for designers.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router)
app.include_router(filters.router)
app.include_router(search.router)
app.include_router(annotations.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "provider": get_provider().name,
        "configured_provider": config.MODEL_PROVIDER,
    }
