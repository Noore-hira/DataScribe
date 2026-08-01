import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from Backend.app.api.chat import router as chat_router
from Backend.app.api.health import router as health_router
from Backend.app.api.report import router as report_router
from Backend.app.api.session import router as session_router
from Backend.app.api.upload import router as upload_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 DataScribe API Starting...")
    yield
    print("🛑 DataScribe API Stopped")


app = FastAPI(
    title="DataScribe API",
    description="Multi-Agent AI Data Science Assistant",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://data-scribe-ai.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # ==========================================================
    # RELAXED HEADERS: Only for Interactive HTML Charts
    # ==========================================================
    if request.url.path.startswith("/charts/") and request.url.path.endswith(".html"):
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Remove X-Frame-Options if it was added by default
        if "X-Frame-Options" in response.headers:
            del response.headers["X-Frame-Options"]
            
        # Relaxed CSP: Allow Plotly scripts and allow framing
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.plot.ly; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https: http:; "
            "frame-ancestors *;"  # <--- Crucial: Allows React iframe to embed this
        )
        return response

    # ==========================================================
    # STRICT HEADERS: For all standard API routes
    # ==========================================================
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Your existing strict CSP
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https: http:; "
        "font-src 'self' data:; "
        "connect-src 'self' https: http:; "
        "frame-ancestors 'none'; "  # <--- Blocks iframes everywhere else
        "base-uri 'self'; "
        "form-action 'self'"
    )
    return response


# ==========================================================
# Static Files
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

STORAGE_DIR = BASE_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

# Executor saves charts here
CHARTS_DIR = Path(os.getenv("LANGGRAPH_ARTIFACTS_DIR", "/tmp/charts"))
CHARTS_DIR.mkdir(parents=True, exist_ok=True)

print(f"Serving charts from: {CHARTS_DIR}")

app.mount("/storage", StaticFiles(directory=str(STORAGE_DIR)), name="storage")
app.mount("/charts", StaticFiles(directory=str(CHARTS_DIR)), name="charts")

# ==========================================================
# Routers
# ==========================================================

app.include_router(health_router, prefix="/api", tags=["Health"])
app.include_router(upload_router, prefix="/api", tags=["Upload"])
app.include_router(chat_router, prefix="/api", tags=["Chat"])
app.include_router(report_router, prefix="/api", tags=["Reports"])
app.include_router(session_router, prefix="/api", tags=["Session"])


@app.get("/")
async def root():
    return {
        "name": "DataScribe API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "charts_directory": str(CHARTS_DIR),
    }