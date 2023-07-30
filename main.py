import spotifyApiConsumer as sac
import chromaticLogic as cl
import database as db
from dotenv import load_dotenv
from flask import Flask, request, Response

load_dotenv()

#flask cors to allow cross origin requests from localhost:4200
from flask_cors import CORS

import os
from FlaskSessionCache import FlaskSessionCacheHandler
from flask import Flask, session, request, redirect
from flask_session import Session
import json

print(os.environ.get("SPOTIPY_CLIENT_ID"))

db.MusicDatabase(os.environ.get("DB_URL"), os.environ.get("DB_NAME"), os.environ.get("DB_COLLECTION"))

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:4200"}})

@app.route("/get_albums_by_chromaticity", methods=["POST"])
def get_albums_by_chromaticity():
    #get body
    body = request.get_json()
    #search in body for access token
    if "token" not in body:
        return Response("No access token provided", status=400)
    if "timeRevision" not in body:
        return Response("No time revision provided", status=400)
    if "quantitySongs" not in body:
        return Response("No quantity songs provided", status=400)
    #get access token
    access_token = body["token"]
    #get time revision
    time_revision = body["timeRevision"]
    #get quantity songs
    quantity_songs = body["quantitySongs"]
    #get top 50 songs
    top_50_songs = sac.get_top_50(access_token, time_revision, quantity_songs)
    xd=cl.retrieve_chromatic_order_from_spotify_data(top_50_songs)
    return Response(json.dumps(xd), status=200, mimetype="application/json")

if __name__ == "__main__":
    app.run(debug=True)