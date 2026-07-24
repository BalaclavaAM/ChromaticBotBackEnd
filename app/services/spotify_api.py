"""Spotify API consumer service"""
import logging

import httpx
from fastapi import HTTPException

logger = logging.getLogger(__name__)

TIME_RANGES = {
    "1m": "short_term",
    "6m": "medium_term",
    "a": "long_term"
}

TOP_TRACKS_URL = "https://api.spotify.com/v1/me/top/tracks"


class SpotifyAPIService:
    """Service for consuming Spotify API"""

    @staticmethod
    async def get_top_tracks(
        http_client: httpx.AsyncClient,
        access_token: str,
        time_revision: str,
        quantity_songs: int
    ) -> dict:
        """Get user's top tracks from Spotify

        Args:
            http_client: Shared async HTTP client
            access_token: Spotify access token
            time_revision: Time period ('1m', '6m', or 'a')
            quantity_songs: Number of songs to retrieve

        Returns:
            Dictionary with Spotify API response containing top tracks

        Raises:
            HTTPException: If access token is invalid or API request fails
        """
        try:
            response = await http_client.get(
                TOP_TRACKS_URL,
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "limit": quantity_songs,
                    "time_range": TIME_RANGES[time_revision]
                }
            )
        except httpx.HTTPError:
            logger.exception("Failed to connect to Spotify API")
            raise HTTPException(status_code=503, detail="Failed to connect to Spotify API")

        if response.status_code == 401:
            raise HTTPException(status_code=401, detail="Invalid or expired access token")

        if response.status_code != 200:
            logger.error("Spotify API error %s: %s", response.status_code, response.text)
            raise HTTPException(status_code=502, detail="Spotify API request failed")

        return response.json()
