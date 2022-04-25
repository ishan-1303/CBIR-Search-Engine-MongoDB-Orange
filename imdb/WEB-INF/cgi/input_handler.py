from packages import *
class InputHandler:
	__form = None

	def __init__(self):
		self.__form = cgi.FieldStorage()

	def __get_file(self):
		return self.__form['file']

	def __get_files(self):
		return self.__form['files']

	def __get_search_term(self):
		return self.__form.getvalue('search_term')

	def __get_database(self):
		return self.__form.getvalue('database')

	def get_cbir_algorithm(self):
		return self.__form.getvalue('algorithm')

	def __get_distance_algorithm(self):
		return self.__form.getvalue('distance_algorithm')

	def __get_number_of_clusters(self):
		return int(self.__form.getvalue('number_of_clusters'))

	def __get_similarity_confidence(self):
		return int(self.__form.getvalue('similarity_confidence'))

	def __get_user_name(self):
		return self.__form.getvalue('username')

	def __get_password(self):
		return self.__form.getvalue('password')

	def get_user_input_text(self):
		database = self.__get_database()
		search_term = self.__get_search_term()

		return database, search_term

	def get_user_input_orange(self):
		database = self.__get_database()
		file = self.__get_file()
		#cbir_algorithm = self.get_cbir_algorithm()
		#number_of_clusters = self.__get_number_of_clusters()
		distance_algorithm = self.__get_distance_algorithm()

		return database, file, distance_algorithm
		
	def get_user_input_admin(self):
		database = self.__get_database()
		files = self.__get_files()
		username = self.__get_user_name()
		password = self.__get_password()
		return database, files, username, password




		





	


