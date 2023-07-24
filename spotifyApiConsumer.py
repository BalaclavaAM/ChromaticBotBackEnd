import requests

def get_top_50(access_token: str)->dict:
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    #get top 50 songs
    top_50_songs = requests.get("https://api.spotify.com/v1/me/top/tracks?limit=15", headers=headers).json()
    if "error" in top_50_songs:
        raise Exception("Invalid access token")
    return top_50_songs