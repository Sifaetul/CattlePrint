"""
CattlePrint Main FastAPI Application.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.core.config import settings
from backend.app.core.database import init_db
from backend.app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema & tables
    await init_db()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration for Flutter Web, Mobile & React clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Storage directory for previewing raw & cropped images
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(settings.STORAGE_DIR)), name="storage")

# Mount Frontend static files
from fastapi.responses import FileResponse
from pathlib import Path

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend"
if (frontend_dir / "index.html").exists():
    @app.get("/app", response_class=FileResponse)
    async def serve_app():
        return FileResponse(str(frontend_dir / "index.html"))

    @app.get("/", response_class=FileResponse)
    async def serve_root():
        return FileResponse(str(frontend_dir / "index.html"))

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)
