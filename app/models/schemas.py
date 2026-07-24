"""Pydantic models for API request/response validation"""
from typing import Literal

from pydantic import BaseModel, Field


class ChromaticityRequest(BaseModel):
    """Request model for getting albums by chromaticity"""
    token: str = Field(..., description="Spotify access token")
    timeRevision: Literal["1m", "6m", "a"] = Field(..., description="Time period: '1m', '6m', or 'a'")
    quantitySongs: int = Field(..., gt=0, le=50, description="Number of songs to retrieve (1-50)")
    sort_mode: Literal["hue", "saturation", "brightness"] = Field(default="hue", description="Sort mode")


class SongInfo(BaseModel):
    """Information about a song"""
    name: str
    artists: str


class AlbumChromaticInfo(BaseModel):
    """Chromatic information about an album"""
    album: str
    image: str
    colors: list[tuple[int, int, int]]
    dominant: tuple[int, int, int]
    color_names: list[str]
    colorfulness: float
    saturation: float
    brightness: float
    songs: list[SongInfo]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    service: str
