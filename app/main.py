"""FastAPI ChromaticBot Backend Main Application"""
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from os import environ

from app.routers import chromatic, health
from app.models.schemas import ChromaticityRequest, AlbumChromaticInfo
from app.services.database import MusicDatabase, get_database

# Load environment variables
load_dotenv()

# Create FastAPI application
app = FastAPI(
    title="ChromaticBot Backend",
    description="API for sorting Spotify albums by chromatic analysis",
    version="2.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[environ.get("CLIENT_ORIGIN", "http://localhost:4200")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chromatic.router)
app.include_router(health.router)


# Legacy endpoint for backward compatibility with frontend
@app.post("/get_albums_by_chromaticity", response_model=list[AlbumChromaticInfo])
async def legacy_get_albums_by_chromaticity(
    request: ChromaticityRequest,
    database: MusicDatabase = Depends(get_database)
) -> list[AlbumChromaticInfo]:
    """Legacy endpoint for backward compatibility

    This endpoint maintains the original API path for existing clients.
    New clients should use /chromatic/albums instead.

    Raises:
        HTTPException: If Spotify API fails or token is invalid
    """
    return await chromatic._get_albums_by_chromaticity_logic(request, database)

# Log MongoDB configuration on startup
@app.on_event("startup")
async def startup_event():
    """Log startup information"""
    db_url = environ.get("DB_URL")
    db_name = environ.get("DB_NAME")
    db_collection = environ.get("DB_COLLECTION")

    if db_url and db_name and db_collection:
        print("MongoDB configuration detected - caching enabled")
    else:
        print("MongoDB variables not provided - running without cache")

    print("ChromaticBot Backend started successfully")


if __name__ == "__main__":
    from uvicorn import run
    run("app.main:app", host="0.0.0.0", port=8080, reload=True)
