import logging

from spotipy import CacheHandler

class FlaskSessionCacheHandler(CacheHandler):
    """
    A cache handler that stores the token info in the session framework
    provided by flask.
    """
    def __init__(self, session, logger=logging.getLogger(__name__)):
        self.session = session
        self.logger = logger

    def get_cached_token(self):
        token_info = None
        try:
            token_info = self.session["token_info"]
        except KeyError:
            self.logger.debug("Token not found in the session")

        return token_info

    def save_token_to_cache(self, token_info):
        try:
            self.session["token_info"] = token_info
        except Exception as e:
            self.logger.warning("Error saving token to cache: " + str(e))