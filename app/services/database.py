"""MongoDB cache service backed by a single client managed by the app lifespan"""
import logging
from typing import Any

from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

logger = logging.getLogger(__name__)


def create_mongo_client(db_url: str, timeout_ms: int = 2000) -> MongoClient | None:
    """Create a MongoClient and verify the server is reachable

    Args:
        db_url: MongoDB connection URL
        timeout_ms: Server selection timeout in milliseconds

    Returns:
        Connected MongoClient, or None if the server is unreachable
    """
    client: MongoClient = MongoClient(db_url, serverSelectionTimeoutMS=timeout_ms)
    try:
        client.admin.command("ping")
        return client
    except PyMongoError:
        logger.exception("MongoDB unreachable - running without cache")
        client.close()
        return None


class MusicDatabase:
    """Cache of album chromatic information

    Every operation degrades to a no-op when the cache is disabled or the
    database fails: a cache problem must never break a request.
    """

    def __init__(self, collection: Collection | None):
        self.collection = collection
        self.enabled = collection is not None

    def ensure_indexes(self) -> None:
        """Create the unique index on id_album used by lookups and upserts"""
        if not self.enabled:
            return
        try:
            self.collection.create_index("id_album", unique=True)
        except PyMongoError:
            logger.exception("Failed to create cache index")

    def get_documents_by_ids(self, album_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Fetch cached documents for the given album IDs in a single query

        Args:
            album_ids: Album IDs to look up

        Returns:
            Mapping of album ID to cached document (missing IDs are absent)
        """
        if not self.enabled or not album_ids:
            return {}
        try:
            cursor = self.collection.find({"id_album": {"$in": album_ids}})
            return {doc["id_album"]: doc for doc in cursor}
        except PyMongoError:
            logger.exception("Cache read failed - continuing without cache")
            return {}

    def upsert_documents(self, documents: list[dict[str, Any]]) -> None:
        """Upsert cached documents keyed by id_album

        Args:
            documents: Documents to store; each must contain "id_album"
        """
        if not self.enabled or not documents:
            return
        try:
            operations = [
                UpdateOne({"id_album": doc["id_album"]}, {"$set": doc}, upsert=True)
                for doc in documents
            ]
            self.collection.bulk_write(operations, ordered=False)
        except PyMongoError:
            logger.exception("Cache write failed - continuing without cache")
