"""Chromatic analysis logic service"""
from numpy import ndarray, sum as np_sum, sqrt, multiply, histogram
from colorthief import ColorThief
from colorsys import rgb_to_hsv
from io import BytesIO
import requests
from app.services.database import MusicDatabase


class ChromaticService:
    """Service for chromatic analysis of album artwork"""

    def __init__(self, database: MusicDatabase):
        """Initialize chromatic service with database dependency

        Args:
            database: MusicDatabase instance for caching
        """
        self.database = database

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
    def histogram_similarity(hist1: ndarray, hist2: ndarray) -> float:
        """Calculate Bhattacharyya distance between two histograms

        Args:
            hist1: First histogram
            hist2: Second histogram

        Returns:
            Similarity score
        """
        return np_sum(sqrt(multiply(hist1, hist2)))

    @staticmethod
    def calculate_histogram(image_colors: ndarray, num_bins: int = 8) -> ndarray:
        """Calculate histogram of colors for an image

        Args:
            image_colors: Array of image colors
            num_bins: Number of histogram bins

        Returns:
            Normalized histogram
        """
        hist, _ = histogram(image_colors, bins=num_bins, range=(0, 256))
        hist = hist.astype(float) / hist.sum()
        return hist

    @staticmethod
    def group_images_by_histogram_similarity(images_info: list[dict], threshold: float) -> list[list[dict]]:
        """Group images by histogram similarity

        Args:
            images_info: List of image information dicts
            threshold: Similarity threshold

        Returns:
            List of grouped images
        """
        groups = []

        for image_info in images_info:
            hist1 = ChromaticService.calculate_histogram(image_info["colors"])
            similar_group = None

            for group in groups:
                hist2 = ChromaticService.calculate_histogram(group[0]["colors"])
                similarity = ChromaticService.histogram_similarity(hist1, hist2)

                if similarity > threshold:
                    similar_group = group
                    break

            if similar_group:
                similar_group.append(image_info)
            else:
                groups.append([image_info])

        return groups

    @staticmethod
    def retrieve_hue(rgb: tuple[int, int, int]) -> float:
        """Retrieve hue from RGB color

        Args:
            rgb: RGB color tuple

        Returns:
            Hue value (0-1)
        """
        r, g, b = rgb
        h, _, _ = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        return h

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
        elif hsv[1] < 0.1:  # If saturation is very low, it's white/gray
            return "white/gray"
        elif 355 <= hue < 10:  # Red
            return "red"
        elif 11 <= hue < 20:  # Red-Orange
            return "red-orange"
        elif 21 <= hue < 40:  # Orange & Brown
            return "orange/brown"
        elif 41 <= hue < 50:  # Orange-Yellow
            return "orange-yellow"
        elif 51 <= hue < 60:  # Yellow
            return "yellow"
        elif 61 <= hue < 80:  # Yellow-Green
            return "yellow-green"
        elif 81 <= hue < 140:  # Green
            return "green"
        elif 141 <= hue < 169:  # Green-Cyan
            return "green-cyan"
        elif 170 <= hue < 200:  # Cyan
            return "cyan"
        elif 201 <= hue < 220:  # Cyan-Blue
            return "cyan-blue"
        elif 221 <= hue < 240:  # Blue
            return "blue"
        elif 241 <= hue < 280:  # Blue-Magenta
            return "blue-magenta"
        elif 281 <= hue < 320:  # Magenta
            return "magenta"
        elif 321 <= hue < 330:  # Magenta-Pink
            return "magenta-pink"
        else:
            return "unknown"

    def retrieve_chromatic_order_from_spotify_data(self, spotify_data: dict[str, any], sort_mode: str = "hue") -> list[dict[str, any]]:
        """Process Spotify data and return albums sorted by chromatic order

        Args:
            spotify_data: Spotify API response with user's top tracks
            sort_mode: Sorting mode - "hue", "saturation", or "brightness"

        Returns:
            List of albums with chromatic information, sorted by specified mode
        """
        new_items = []
        album_position_map = {}

        for item in spotify_data["items"]:
            album_id = item["album"]["id"]
            position = -1

            # Check if album already processed
            if album_id in album_position_map:
                position = album_position_map[album_id]
            else:
                album_position_map[album_id] = len(new_items)

            if position == -1:
                # Try to get from cache
                chromatic_info = self.database.get_document_by_id(album_id)
                new_item = {}
                image_url = item["album"]["images"][0]["url"]

                if chromatic_info is None:
                    # Download image in memory (stateless - no disk I/O)
                    response = requests.get(image_url, timeout=10)
                    response.raise_for_status()
                    image_bytes = BytesIO(response.content)

                    # Extract colors from image (no cache available)
                    palette, dominant = self.extract_color_palette_and_dominant(image_bytes)

                    # Calculate HSV values
                    h, s, v = rgb_to_hsv(dominant[0] / 255.0, dominant[1] / 255.0, dominant[2] / 255.0)
                    colorfulness = h  # Hue
                    saturation = s    # Saturation
                    brightness = v    # Brightness (Value)

                    # Save to database cache
                    self.database.create_document(album_id, dominant, palette, colorfulness)
                else:
                    # Use cached chromatic info
                    palette = chromatic_info["palette_colors"]
                    dominant = chromatic_info["dominant_color"]
                    colorfulness = chromatic_info["colorfulness"]
                    # Calculate saturation and brightness from cached dominant color
                    h, s, v = rgb_to_hsv(dominant[0] / 255.0, dominant[1] / 255.0, dominant[2] / 255.0)
                    saturation = s
                    brightness = v

                new_item["album"] = item["album"]["name"]
                new_item["image"] = item["album"]["images"][0]["url"]
                new_item["colors"] = palette
                new_item["dominant"] = dominant
                new_item["color_names"] = [self.classify_color(color) for color in palette]
                new_item["colorfulness"] = colorfulness
                new_item["saturation"] = saturation
                new_item["brightness"] = brightness
                new_item["songs"] = []
                new_items.append(new_item)
                position = album_position_map[album_id]

            # Add song to album
            album_item = new_items[position]
            song_info = {
                "name": item["name"],
                "artists": ", ".join([artist["name"] for artist in item["artists"]])
            }
            album_item["songs"].append(song_info)

        # Sort by chromatic order based on selected mode
        if sort_mode == "saturation":
            new_items.sort(key=lambda x: x["saturation"], reverse=True)
        elif sort_mode == "brightness":
            new_items.sort(key=lambda x: x["brightness"], reverse=True)
        else:  # "hue" (default)
            new_items.sort(key=lambda x: x["colorfulness"])

        return new_items
