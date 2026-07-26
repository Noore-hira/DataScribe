from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from Backend.app.api.chat import router as chat_router
from Backend.app.api.health import router as health_router
from Backend.app.api.report import router as report_router
from Backend.app.api.session import router as session_router
from Backend.app.api.upload import router as upload_router


# ==========================================================
# Lifespan
# ==========================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / Shutdown events.
    """

    print("🚀 DataScribe API Starting...")

    yield

    print("🛑 DataScribe API Stopped")


# ==========================================================
# FastAPI App
# ==========================================================

app = FastAPI(
    title="DataScribe API",
    description="Multi-Agent AI Data Science Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

# ==========================================================
# CORS
# ==========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================
# Static Files
# ==========================================================

import os

# Ensure absolute directory resolution so it never fails regardless of where uvicorn is launched
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHARTS_DIR = os.path.join(BASE_DIR, "charts") # Adjust if charts are inside Backend/charts

# If your charts folder is inside Backend/app or root:
# CHARTS_DIR = os.path.abspath(os.path.join(BASE_DIR, "../charts"))

os.makedirs(CHARTS_DIR, exist_ok=True)

app.mount(
    "/charts",
    StaticFiles(directory=CHARTS_DIR),
    name="charts",
)

app.mount(
    "/reports",
    StaticFiles(directory="Backend/storage/reports"),
    name="reports",
)

# ==========================================================
# Routers
# ==========================================================

app.include_router(
    health_router,
    prefix="/api",
    tags=["Health"],
)

app.include_router(
    upload_router,
    prefix="/api",
    tags=["Upload"],
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["Chat"],
)

app.include_router(
    report_router,
    prefix="/api",
    tags=["Reports"],
)

app.include_router(
    session_router,
    prefix="/api",
    tags=["Session"],
)

# ==========================================================
# Root
# ==========================================================

@app.get("/")
async def root():

    return {
        "name": "DataScribe API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }