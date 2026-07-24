"""Chromatic endpoints router"""
import logging

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request

from app.models.schemas import ChromaticityRequest, AlbumChromaticInfo
from app.services.database import MusicDatabase
from app.services.spotify_api import SpotifyAPIService
from app.services.chromatic_logic import ChromaticService

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chromatic",
    tags=["chromatic"]
)


def get_database(request: Request) -> MusicDatabase:
    """FastAPI dependency returning the cache backed by the shared Mongo client"""
    return MusicDatabase(request.app.state.cache_collection)


def get_http_client(request: Request) -> httpx.AsyncClient:
    """FastAPI dependency returning the shared async HTTP client"""
    return request.app.state.http_client


@router.post("/albums", response_model=list[AlbumChromaticInfo])
async def get_albums_by_chromaticity(
    request: ChromaticityRequest,
    database: MusicDatabase = Depends(get_database),
    http_client: httpx.AsyncClient = Depends(get_http_client)
) -> list[dict]:
    """Get albums sorted by chromaticity from user's top tracks

    Args:
        request: Request containing Spotify token, time revision, and quantity
        database: Database dependency injection
        http_client: Shared async HTTP client

    Returns:
        List of albums with chromatic information sorted by the selected mode

    Raises:
        HTTPException: If Spotify API fails or token is invalid
    """
    try:
        top_tracks = await SpotifyAPIService.get_top_tracks(
            http_client,
            access_token=request.token,
            time_revision=request.timeRevision,
            quantity_songs=request.quantitySongs
        )

        chromatic_service = ChromaticService(database, http_client)
        return await chromatic_service.retrieve_chromatic_order_from_spotify_data(
            top_tracks,
            sort_mode=request.sort_mode
        )

    except HTTPException:
        # Re-raise HTTPExceptions from services
        raise
    except Exception:
        logger.exception("Unhandled error while processing chromatic request")
        raise HTTPException(status_code=500, detail="Internal server error")
