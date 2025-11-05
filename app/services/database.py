"""MongoDB database service with dependency injection"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from os import environ


class MusicDatabase:
    """MongoDB service for storing album chromatic information"""

    def __init__(self, db_url: str | None = None, db_name: str | None = None, collection_name: str | None = None):
        """Initialize MongoDB connection

        Args:
            db_url: MongoDB connection URL
            db_name: Database name
            collection_name: Collection name
        """
        # Check if MongoDB configuration is provided
        if db_url and db_name and collection_name:
            try:
                self.client: MongoClient = MongoClient(db_url)
                self.db: Database = self.client[db_name]
                self.collection: Collection = self.db[collection_name]
                self.enabled = True
                print("MongoDB connection established successfully")
            except Exception as e:
                print(f"MongoDB connection failed: {e}")
                self.enabled = False
                self.client = None
                self.db = None
                self.collection = None
        else:
            print("MongoDB configuration not provided - running without cache")
            self.enabled = False
            self.client = None
            self.db = None
            self.collection = None

    def create_document(self, id_album: str, dominant_color: tuple, palette_colors: list, colorfulness: float) -> str | None:
        """Create a new document in the collection

        Args:
            id_album: Album ID
            dominant_color: Dominant color RGB tuple
            palette_colors: List of palette colors
            colorfulness: Colorfulness metric

        Returns:
            Inserted document ID or None if DB not enabled
        """
        if not self.enabled:
            return None

        document = {
            "id_album": id_album,
            "dominant_color": dominant_color,
            "palette_colors": palette_colors,
            "colorfulness": colorfulness
        }

        result = self.collection.insert_one(document)
        return str(result.inserted_id)

    def get_document_by_id(self, id_album: str) -> dict[str, any] | None:
        """Find a document by album ID

        Args:
            id_album: Album ID to search for

        Returns:
            Document dict or None if not found or DB not enabled
        """
        if not self.enabled:
            return None

        document = self.collection.find_one({"id_album": id_album})
        return document

    def get_all_documents(self) -> list[dict[str, any]]:
        """Get all documents from the collection

        Returns:
            List of all documents, empty list if DB not enabled
        """
        if not self.enabled:
            return []

        documents = list(self.collection.find())
        return documents

    def delete_document_by_id(self, id_album: str) -> int:
        """Delete a document by album ID

        Args:
            id_album: Album ID to delete

        Returns:
            Number of deleted documents (0 or 1)
        """
        if not self.enabled:
            return 0

        result = self.collection.delete_one({"id_album": id_album})
        return result.deleted_count

    def update_document(self, id_album: str, updates: dict[str, any]) -> int:
        """Update a document by album ID

        Args:
            id_album: Album ID to update
            updates: Dictionary of fields to update

        Returns:
            Number of modified documents
        """
        if not self.enabled:
            return 0

        result = self.collection.update_one({"id_album": id_album}, {"$set": updates})
        return result.modified_count

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()


# Dependency to get database instance
def get_database() -> MusicDatabase:
    """FastAPI dependency to get database instance

    Returns:
        MusicDatabase instance configured from environment variables
    """
    db_url = environ.get("DB_URL")
    db_name = environ.get("DB_NAME")
    db_collection = environ.get("DB_COLLECTION")

    return MusicDatabase(db_url, db_name, db_collection)
