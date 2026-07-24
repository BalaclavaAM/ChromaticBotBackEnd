"""FastAPI ChromaticBot Backend Main Application"""
import logging
from contextlib import asynccontextmanager
from os import environ

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import chromatic, health
from app.models.schemas import AlbumChromaticInfo
from app.services.database import MusicDatabase, create_mongo_client

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=environ.get("LOG_LEVEL", "info").upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in environ.get("CLIENT_ORIGIN", "http://localhost:4200").split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create and tear down the shared Mongo and HTTP clients"""
    app.state.mongo_client = None
    app.state.cache_collection = None

    db_url = environ.get("DB_URL")
    db_name = environ.get("DB_NAME")
    db_collection = environ.get("DB_COLLECTION")

    if db_url and db_name and db_collection:
        mongo_client = create_mongo_client(db_url)
        if mongo_client is not None:
            app.state.mongo_client = mongo_client
            app.state.cache_collection = mongo_client[db_name][db_collection]
            MusicDatabase(app.state.cache_collection).ensure_indexes()
            logger.info("MongoDB cache enabled")
    else:
        logger.info("MongoDB variables not provided - running without cache")

    app.state.http_client = httpx.AsyncClient(timeout=10, follow_redirects=True)
    logger.info("ChromaticBot Backend started (allowed origins: %s)", ALLOWED_ORIGINS)

    yield

    await app.state.http_client.aclose()
    if app.state.mongo_client is not None:
        app.state.mongo_client.close()


# Create FastAPI application
app = FastAPI(
    title="ChromaticBot Backend",
    description="API for sorting Spotify albums by chromatic analysis",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chromatic.router)
app.include_router(health.router)

# Legacy path kept for backward compatibility with existing clients;
# new clients should use /chromatic/albums
app.add_api_route(
    "/get_albums_by_chromaticity",
    chromatic.get_albums_by_chromaticity,
    methods=["POST"],
    response_model=list[AlbumChromaticInfo],
    tags=["chromatic"],
    deprecated=True,
)


if __name__ == "__main__":
    from uvicorn import run
    run("app.main:app", host="0.0.0.0", port=8080, reload=True)
