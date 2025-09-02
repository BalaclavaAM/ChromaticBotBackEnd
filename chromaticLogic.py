import numpy as np
import urllib.request as urllib2
import os
import colorthief
import database as db

def extract_color_palette_and_dominant(image_path):
    color_thief = colorthief.ColorThief(image_path)
    palette = color_thief.get_palette(color_count=6)
    dominant = color_thief.get_color(quality=7)
    return (palette, dominant)

def histogram_similarity(hist1, hist2):
    # Calculate the Bhattacharyya distance between two histograms
    return np.sum(np.sqrt(np.multiply(hist1, hist2)))

def calculate_histogram(image_colors, num_bins=8):
    # Calculate the histogram of colors for an image
    hist, _ = np.histogram(image_colors, bins=num_bins, range=(0, 256))
    hist = hist.astype(float) / hist.sum()
    return hist

def group_images_by_histogram_similarity(images_info, threshold):
    groups = []

    for image_info in images_info:
        hist1 = calculate_histogram(image_info["colors"])

        similar_group = None

        for group in groups:
            hist2 = calculate_histogram(group[0]["colors"])
            similarity = histogram_similarity(hist1, hist2)

            if similarity > threshold:
                similar_group = group
                break

        if similar_group:
            similar_group.append(image_info)
        else:
            groups.append([image_info])

    return groups

from colorsys import rgb_to_hsv

def retrieve_hue(rgb):
    r, g, b = rgb
    h, _, _ = rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h

def classify_color(rgb)->str:
    # The uidea is classify based in the 8 intervals of the hue
    # and retrieve the color name
    # 0-45 red
    # 45-90 orange
    # 90-135 yellow
    # 135-180 green
    # 180-225 cyan
    # 225-270 blue
    # 270-315 magenta
    # 315-360 red
    #check if the color is black or white
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

def retrieve_chromatic_order_from_spotify_data(spotify_data: dict) -> list:
    new_items = []
    diccionario_temporal = {}
    database = db.MusicDatabase()
    for item in spotify_data["items"]:
        position = -1
        # buscar posicion del album en el diccionario
        if item["album"]["id"] in diccionario_temporal:
            position = diccionario_temporal[item["album"]["id"]]
        else:
            diccionario_temporal[item["album"]["id"]] = len(new_items)
        if position == -1:
            chromatic_info=database.get_document_by_id(item["album"]["id"])
            new_item = {}
            image_url = item["album"]["images"][0]["url"]
            image_path = "./imageCache/" + item["id"] + ".jpg"
            
            # Create imageCache directory if it doesn't exist
            os.makedirs("./imageCache", exist_ok=True)
            
            if not os.path.isfile(image_path):
                urllib2.urlretrieve(image_url, image_path)
            if chromatic_info is None:
                color_palette_dominant = extract_color_palette_and_dominant(image_path)
                colorfuness = retrieve_hue(color_palette_dominant[1])
                database.create_document(item["album"]["id"], color_palette_dominant[1], color_palette_dominant[0], colorfuness)
            else:
                color_palette_dominant = chromatic_info["palette_colors"], chromatic_info["dominant_color"]
                colorfuness = chromatic_info["colorfulness"]
            new_item["album"] = item["album"]["name"]
            new_item["image"] = item["album"]["images"][0]["url"]
            new_item["colors"] = color_palette_dominant[0]
            new_item["dominant"] = color_palette_dominant[1]
            new_item["color_names"] = [classify_color(color) for color in color_palette_dominant[0]]
            new_item["colorfulness"] = colorfuness
            new_items.append(new_item)
            position = diccionario_temporal[item["album"]["id"]]
        new_item = new_items[position]
        lista_canciones = new_item.get("songs", [])
        lista_canciones.append({"name": item["name"], "artists": ", ".join([artist["name"] for artist in item["artists"]])})
        new_item["songs"] = lista_canciones

    # Sort new_items based on the chromatic order (colorfulness of dominant color)
    new_items.sort(key=lambda x: x["colorfulness"])

    return new_items

