from pymongo import MongoClient

class MusicDatabase:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(MusicDatabase, cls).__new__(cls)
            cls._instance._init_singleton(*args, **kwargs)
        return cls._instance

    def _init_singleton(self, db_url, db_name, collection_name):
        self.client = MongoClient(db_url)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def create_document(self, id_album, dominant_color, palette_colors, colorfulness):
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
        # Find a document by its id_album
        document = self.collection.find_one({"id_album": id_album})
        return document

    def get_all_documents(self):
        # Get all documents from the collection
        documents = list(self.collection.find())
        return documents

    def delete_document_by_id(self, id_album):
        # Delete a document by its id_album
        result = self.collection.delete_one({"id_album": id_album})
        return result.deleted_count

    def update_document(self, id_album, updates):
        # Update a document by its id_album
        result = self.collection.update_one({"id_album": id_album}, {"$set": updates})
        return result.modified_count
