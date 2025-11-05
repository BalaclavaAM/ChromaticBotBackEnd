"""Spotify API consumer service"""
from requests import get, exceptions
from fastapi import HTTPException


TIME_RANGES = {
    "1m": "short_term",
    "6m": "medium_term",
    "a": "long_term"
}


class SpotifyAPIService:
    """Service for consuming Spotify API"""

    @staticmethod
    def get_top_tracks(access_token: str, time_revision: str, quantity_songs: int) -> dict:
        """Get user's top tracks from Spotify

        Args:
            access_token: Spotify access token
            time_revision: Time period ('1m', '6m', or 'a')
            quantity_songs: Number of songs to retrieve

        Returns:
            Dictionary with Spotify API response containing top tracks

        Raises:
            HTTPException: If access token is invalid or API request fails
        """
        if time_revision not in TIME_RANGES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid time revision. Must be one of: {list(TIME_RANGES.keys())}"
            )

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        try:
            response = get(
                f"https://api.spotify.com/v1/me/top/tracks",
                headers=headers,
                params={
                    "limit": quantity_songs,
                    "time_range": TIME_RANGES[time_revision]
                },
                timeout=10
            )

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid or expired access token")

            if response.status_code != 200:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Spotify API error: {response.text}"
                )

            data = response.json()

            if "error" in data:
                raise HTTPException(status_code=400, detail=f"Spotify API error: {data['error']}")

            return data

        except exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"Failed to connect to Spotify API: {str(e)}")
