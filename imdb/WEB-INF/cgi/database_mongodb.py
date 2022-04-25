from packages import *
from pymongo import TEXT

class DatabaseMongoDB:
	__database = None
	__fs = None
	
	def initialize(self, host, db, username=None, password=None):
		connection = None
		if(username != None and password != None):
			connection = MongoClient(host, username=username, password=password, authSource=db, authMechanism='SCRAM-SHA-256') 
		else:
			connection = MongoClient(host)

		self.__database = connection[db]
		#return self.__database

	def initialize_gridFS(self):
		self.__fs = gridfs.GridFS(self.__database)
	
	def insert(self, collection, data):
		return self.__database[collection].insert(data)
	
	def find(self, collection, query):
		return self.__database[collection].find(query)
	
	def find_one(self, collection, query):
		return self.__database[collection].find_one(query)
	
	def update_one(self, collection, query, data):
		return self.__database[collection].update_one(query, data)
	
	def put_file_gridFS(self, media_file):
		file = open(media_file, 'rb');
		return self.__fs.put(file, filename = os.path.basename(media_file))
	
	def get_file_gridFS(self,filename):
		out = self.__database['fs.files'].find_one({'filename':filename})
		if(out is None):
			return None
			
		return self.__fs.get(out['_id'])
	
	def delete(self, collection, query):
		return self.__database[collection].delete_one(query)

	def create_text_index(self, collection, field):
		return self.__database[collection].create_index([(field, TEXT)], default_language='english')



