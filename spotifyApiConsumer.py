import requests

TIME = {
    "1m" : "short_term",
    "6m" : "medium_term",
    "a" : "long_term"
}

def get_top_50(access_token: str, time_revision: str, quantity_songs: str)->dict:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    #get top 50 songs
    top_50_songs = requests.get(f"https://api.spotify.com/v1/me/top/tracks?limit={quantity_songs}&time_range={TIME[time_revision]}", headers=headers).json()
    if "error" in top_50_songs:
        raise ValueError("Invalid access token")
    return top_50_songs