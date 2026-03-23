"""
FastAPI application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.routes import stream, director, content, platform, logs, danmaku, ai_agent, layers
from api.app_state import init_state, cleanup_state, get_streamer, get_director
from core.config import get_settings
from core.logger import setup_logger, get_logger

settings = get_settings()
logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    # Startup
    setup_logger(settings.LOGS_DIR)
    
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    
    # Initialize services
    init_state()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    cleanup_state()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered digital human livestream system",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(stream.router, prefix=f"{settings.API_PREFIX}/stream", tags=["Stream"])
app.include_router(director.router, prefix=f"{settings.API_PREFIX}/director", tags=["Director"])
app.include_router(content.router, prefix=f"{settings.API_PREFIX}/content", tags=["Content"])
app.include_router(platform.router, prefix=f"{settings.API_PREFIX}/platform", tags=["Platform"])
app.include_router(logs.router, prefix=f"{settings.API_PREFIX}/logs", tags=["Logs"])
app.include_router(danmaku.router, prefix=f"{settings.API_PREFIX}/danmaku", tags=["Danmaku"])
app.include_router(ai_agent.router, prefix=f"{settings.API_PREFIX}/ai", tags=["AI"])
app.include_router(layers.router, prefix=f"{settings.API_PREFIX}/layers", tags=["Layers"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    streamer = get_streamer()
    director = get_director()
    
    return {
        "status": "healthy",
        "streamer": streamer.status.to_dict() if streamer else None,
        "director": director.status.to_dict() if director else None,
    }
