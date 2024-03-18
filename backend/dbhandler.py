from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import os, logging, sys

class DBHandler:
    def __init__(self) -> None:
        try:
            self.uri = f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASS')}@{os.getenv('MONGO_CLUSTER_URI')}/{os.getenv('MONGO_DB_NAME')}?retryWrites=true&w=majority&appName=Cluster0"
            # Create a new client and connect to the server
            self.client = MongoClient(self.uri, server_api=ServerApi('1'))
            self.db=self.client[os.getenv('MONGO_DB_NAME')]
            self.collection_name = 'files'
            self.files_collection = self.db[self.collection_name]
            _, isError = self.initial_check()
            if isError: raise Exception('Ping to MongoDB Failed.')
        except Exception as ex:
            print(f'Error for setuping up DB config: {str(ex)}. Make sure .env is setup properly.')
            logging.critical(f'Error for setuping up DB config: {str(ex)}. Make sure .env is setup properly.')
            sys.exit()
        
    def initial_check(self):
        # Send a ping to confirm a successful connection
        try:
            self.client.admin.command('ping')
            logging.info("Pinged your deployment. You successfully connected to MongoDB!")
            return 'OK', False
        except Exception as e:
            logging.critical(e)
            return str(e), True
            
    def insert_one(self, data):
        try:
            self.files_collection.insert_one(data)
            logging.info('Inserted successfully')
        except Exception as e:
            logging.error(e)
            
    def check_hash_exists(self, file_hash):
        return self.files_collection.find_one({"filehash": file_hash}) is not None