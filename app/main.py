"""Main FastAPI application."""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from app.api import scans
from app.config import settings
from app.db import engine, Base
from app.services.worker import get_worker

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting application")
    
    # Create database tables
    logger.info("Creating database tables")
    Base.metadata.create_all(bind=engine)
    
    # Start background worker
    logger.info("Starting background worker")
    worker = get_worker()
    worker.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    worker.stop()


# Create FastAPI app
app = FastAPI(
    title="Google Maps No-Website Finder",
    description="Find businesses on Google Maps without websites",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include routers
app.include_router(scans.router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Render dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/scans/{scan_id}", response_class=HTMLResponse)
async def scan_detail(request: Request, scan_id: str):
    """Render scan detail page."""
    return templates.TemplateResponse(
        "scan_detail.html",
        {"request": request, "scan_id": scan_id}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
