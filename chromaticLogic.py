import math
import cv2
import numpy as np
from sklearn.cluster import KMeans
import urllib.request as urllib2
import os
import colorthief

def extract_color_palette_and_dominant(image_path):
    color_thief = colorthief.ColorThief(image_path)
    palette = color_thief.get_palette(color_count=6)
    dominant = color_thief.get_color(quality=5)
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

def retrieve_chromatic_order_from_spotify_data(spotify_data: dict)->list:
    new_items=[]
    diccionario_temporal={}
    for item in spotify_data["items"]:
        position = -1
        #buscar posicion del album en el diccionario
        if item["album"]["id"] in diccionario_temporal:
            position = diccionario_temporal[item["album"]["id"]]
        else:
            diccionario_temporal[item["album"]["id"]] = len(diccionario_temporal)
            position = diccionario_temporal[item["album"]["id"]]
        if position != -1:
            new_item = {}
            image_url = item["album"]["images"][0]["url"]
            image_path = "./imageCache/" + item["id"] + ".jpg"
            if (not os.path.isfile(image_path)):
                urllib2.urlretrieve(image_url, image_path)
            color_palette_dominant = extract_color_palette_and_dominant(image_path)
            new_item["album"] = item["album"]["name"]
            new_item["image"] = item["album"]["images"][0]["url"]
            new_item["colors"] = color_palette_dominant[0]
            new_item["dominant"] = color_palette_dominant[1]
            new_items.append(new_item)
        new_item=new_items[position]
        lista_canciones = new_item.get("songs", [])
        lista_canciones.append({"name": item["name"], "artists": ", ".join([artist["name"] for artist in item["artists"]])})
        new_item["songs"] = lista_canciones
    return group_images_by_histogram_similarity(new_items, 0.7)
