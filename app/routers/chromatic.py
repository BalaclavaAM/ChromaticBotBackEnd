"""Chromatic endpoints router"""
from fastapi import APIRouter, Depends, HTTPException
from app.models.schemas import ChromaticityRequest, AlbumChromaticInfo
from app.services.database import MusicDatabase, get_database
from app.services.spotify_api import SpotifyAPIService
from app.services.chromatic_logic import ChromaticService

router = APIRouter(
    prefix="/chromatic",
    tags=["chromatic"]
)


async def _get_albums_by_chromaticity_logic(
    request: ChromaticityRequest,
    database: MusicDatabase
) -> list[AlbumChromaticInfo]:
    """Internal logic for getting albums by chromaticity

    Args:
        request: Request containing Spotify token, time revision, and quantity
        database: Database dependency injection

    Returns:
        List of albums with chromatic information sorted by colorfulness

    Raises:
        HTTPException: If Spotify API fails or token is invalid
    """
    try:
        # Get top tracks from Spotify
        spotify_service = SpotifyAPIService()
        top_tracks = spotify_service.get_top_tracks(
            access_token=request.token,
            time_revision=request.timeRevision,
            quantity_songs=request.quantitySongs
        )

        # Process chromatic information
        chromatic_service = ChromaticService(database)
        chromatic_data = chromatic_service.retrieve_chromatic_order_from_spotify_data(
            top_tracks,
            sort_mode=request.sort_mode
        )

        return chromatic_data

    except HTTPException:
        # Re-raise HTTPExceptions from services
        raise
    except Exception as e:
        # Catch any unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post("/albums", response_model=list[AlbumChromaticInfo])
async def get_albums_by_chromaticity(
    request: ChromaticityRequest,
    database: MusicDatabase = Depends(get_database)
) -> list[AlbumChromaticInfo]:
    """Get albums sorted by chromaticity from user's top tracks

    Args:
        request: Request containing Spotify token, time revision, and quantity
        database: Database dependency injection

    Returns:
        List of albums with chromatic information sorted by colorfulness

    Raises:
        HTTPException: If Spotify API fails or token is invalid
    """
    return await _get_albums_by_chromaticity_logic(request, database)
