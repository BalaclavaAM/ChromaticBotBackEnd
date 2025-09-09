from pymongo import MongoClient

class MusicDatabase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MusicDatabase, cls).__new__(cls)
            cls._instance._init_singleton(*args, **kwargs)
        return cls._instance

    def _init_singleton(self, db_url, db_name, collection_name):
        # Check if MongoDB configuration is provided
        if db_url and db_name and collection_name:
            try:
                self.client = MongoClient(db_url)
                self.db = self.client[db_name]
                self.collection = self.db[collection_name]
                self.enabled = True
                print("MongoDB connection established successfully")
            except Exception as e:
                print(f"MongoDB connection failed: {e}")
                self.enabled = False
        else:
            print("MongoDB configuration not provided - running without cache")
            self.enabled = False

    def create_document(self, id_album, dominant_color, palette_colors, colorfulness):
        if not self.enabled:
            return None
        # Create a dictionary representing the document
        document = {
            "id_album": id_album,
            "dominant_color": dominant_color,
            "palette_colors": palette_colors,
            "colorfulness": colorfulness
        }

        # Insert the document into the collection
        self.collection.insert_one(document)

    def get_document_by_id(self, id_album):
        if not self.enabled:
            return None
        # Find a document by its id_album
        document = self.collection.find_one({"id_album": id_album})
        return document

    def get_all_documents(self):
        if not self.enabled:
            return []
        # Get all documents from the collection
        documents = list(self.collection.find())
        return documents

    def delete_document_by_id(self, id_album):
        if not self.enabled:
            return 0
        # Delete a document by its id_album
        result = self.collection.delete_one({"id_album": id_album})
        return result.deleted_count

    def update_document(self, id_album, updates):
        if not self.enabled:
            return 0
        # Update a document by its id_album
        result = self.collection.update_one({"id_album": id_album}, {"$set": updates})
        return result.modified_count
