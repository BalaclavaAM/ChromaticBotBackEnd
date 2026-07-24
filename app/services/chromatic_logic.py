"""Chromatic analysis logic service"""
import asyncio
import logging
from colorsys import rgb_to_hsv
from io import BytesIO
from typing import Any

import httpx
from colorthief import ColorThief

from app.services.database import MusicDatabase

logger = logging.getLogger(__name__)

# Cap on concurrent artwork downloads per request, to avoid hammering
# Spotify's CDN and to bound memory usage
MAX_CONCURRENT_DOWNLOADS = 8


class ChromaticService:
    """Service for chromatic analysis of album artwork"""

    def __init__(self, database: MusicDatabase, http_client: httpx.AsyncClient):
        """Initialize chromatic service

        Args:
            database: MusicDatabase instance for caching
            http_client: Shared async HTTP client for artwork downloads
        """
        self.database = database
        self.http_client = http_client

    @staticmethod
    def extract_color_palette_and_dominant(image_source: str | BytesIO) -> tuple[list[tuple[int, int, int]], tuple[int, int, int]]:
        """Extract color palette and dominant color from image

        Args:
            image_source: Path to image file or BytesIO object

        Returns:
            Tuple of (palette, dominant_color)
        """
        color_thief = ColorThief(image_source)
        palette = color_thief.get_palette(color_count=6)
        dominant = color_thief.get_color(quality=7)
        return (palette, dominant)

    @staticmethod
    def classify_color(rgb: tuple[int, int, int]) -> str:
        """Classify color based on HSV values

        Args:
            rgb: RGB color tuple

        Returns:
            Color classification string
        """
        hsv = rgb_to_hsv(rgb[0] / 255.0, rgb[1] / 255.0, rgb[2] / 255.0)
        hue = hsv[0] * 360

        if hsv[2] < 0.1:  # If value is very low, it's black
            return "black"
        if hsv[1] < 0.1:  # If saturation is very low, it's white/gray
            return "white/gray"
        if hue >= 355 or hue < 10:
            return "red"
        if hue < 20:
            return "red-orange"
        if hue < 40:
            return "orange/brown"
        if hue < 50:
            return "orange-yellow"
        if hue < 60:
            return "yellow"
        if hue < 80:
            return "yellow-green"
        if hue < 140:
            return "green"
        if hue < 169:
            return "green-cyan"
        if hue < 200:
            return "cyan"
        if hue < 220:
            return "cyan-blue"
        if hue < 240:
            return "blue"
        if hue < 280:
            return "blue-magenta"
        if hue < 320:
            return "magenta"
        return "magenta-pink"  # 320-355: pink hues up to the red wrap-around

    async def _analyze_album(self, album_id: str, image_url: str, semaphore: asyncio.Semaphore) -> dict[str, Any] | None:
        """Download an album's artwork and extract its chromatic information

        Args:
            album_id: Spotify album ID
            image_url: Artwork URL
            semaphore: Limits concurrent downloads

        Returns:
            Cache-shaped document, or None if download/analysis failed
        """
        async with semaphore:
            try:
                response = await self.http_client.get(image_url)
                response.raise_for_status()
            except httpx.HTTPError:
                logger.warning("Failed to download artwork for album %s", album_id)
                return None

        try:
            # ColorThief/Pillow work is CPU-bound: run it off the event loop
            palette, dominant = await asyncio.to_thread(
                self.extract_color_palette_and_dominant, BytesIO(response.content)
            )
        except Exception:
            logger.exception("Color analysis failed for album %s", album_id)
            return None

        hue, _, _ = rgb_to_hsv(dominant[0] / 255.0, dominant[1] / 255.0, dominant[2] / 255.0)
        return {
            "id_album": album_id,
            "dominant_color": list(dominant),
            "palette_colors": [list(color) for color in palette],
            # Legacy field name kept for cache/API compatibility: holds the hue
            "colorfulness": hue,
        }

    async def retrieve_chromatic_order_from_spotify_data(self, spotify_data: dict[str, Any], sort_mode: str = "hue") -> list[dict[str, Any]]:
        """Process Spotify data and return albums sorted by chromatic order

        Args:
            spotify_data: Spotify API response with user's top tracks
            sort_mode: Sorting mode - "hue", "saturation", or "brightness"

        Returns:
            List of albums with chromatic information, sorted by specified mode
        """
        # Group tracks by album, keeping only albums with artwork
        albums: dict[str, dict[str, Any]] = {}
        for item in spotify_data["items"]:
            album = item["album"]
            album_id = album["id"]
            if not album.get("images"):
                continue  # local tracks or releases without artwork can't be analyzed
            if album_id not in albums:
                albums[album_id] = {
                    "album": album["name"],
                    "image": album["images"][0]["url"],
                    "songs": [],
                }
            albums[album_id]["songs"].append({
                "name": item["name"],
                "artists": ", ".join(artist["name"] for artist in item["artists"]),
            })

        album_ids = list(albums)
        cached = await asyncio.to_thread(self.database.get_documents_by_ids, album_ids)

        # Analyze uncached albums concurrently
        missing = [album_id for album_id in album_ids if album_id not in cached]
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)
        analyzed = await asyncio.gather(*(
            self._analyze_album(album_id, albums[album_id]["image"], semaphore)
            for album_id in missing
        ))
        fresh = [doc for doc in analyzed if doc is not None]
        if fresh:
            await asyncio.to_thread(self.database.upsert_documents, fresh)
            cached.update({doc["id_album"]: doc for doc in fresh})

        results = []
        for album_id in album_ids:
            doc = cached.get(album_id)
            if doc is None:
                continue  # artwork failed to analyze: drop the album, not the request
            dominant = doc["dominant_color"]
            _, saturation, brightness = rgb_to_hsv(
                dominant[0] / 255.0, dominant[1] / 255.0, dominant[2] / 255.0
            )
            info = albums[album_id]
            results.append({
                "album": info["album"],
                "image": info["image"],
                "colors": doc["palette_colors"],
                "dominant": dominant,
                "color_names": [self.classify_color(color) for color in doc["palette_colors"]],
                "colorfulness": doc["colorfulness"],
                "saturation": saturation,
                "brightness": brightness,
                "songs": info["songs"],
            })

        if sort_mode == "saturation":
            results.sort(key=lambda x: x["saturation"], reverse=True)
        elif sort_mode == "brightness":
            results.sort(key=lambda x: x["brightness"], reverse=True)
        else:  # "hue" (default)
            results.sort(key=lambda x: x["colorfulness"])

        return results
