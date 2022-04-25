from packages import *
from input_handler import InputHandler
from cbir import CBIR
from data_handler import DataHandler

class Result():
	__ui = None
	cbir_algorithm = None
	def __init__(self):
		self.__ui = InputHandler()

		self.cbir_algorithm = self.__ui.get_cbir_algorithm()


	def run_cbir_orange(self):
		data_handle = None
		try:
			start_time = time.time()
			database, image_file, distance_algorithm = self.__ui.get_user_input_orange()

			cbir = CBIR(database)
			data_handle = DataHandler(database, lab = False, username=None, password=None)

			client_id = data_handle.create_random_client()
			directory_main = '../../temp_files'
			directory = directory_main + "/" + str(client_id)

			os.makedirs(directory)
			query_image_encoded = data_handle.process_image_file(directory, image_file)

			query_image_table = cbir.create_image_table(directory)
			query_image_embeddings = cbir.extract_features_from_images(self.cbir_algorithm, query_image_table, directory)

			image_table = cbir.create_image_table_from_csv()
			image_file_paths = cbir.get_image_file_paths(directory)

			image_embeddings = data_handle.get_features_from_database(image_table, self.cbir_algorithm)

			image_embedder_table = cbir.prepare_embedding_table(image_embeddings, query_image_embeddings)
			distance_matrix = cbir.compute_distance(image_embedder_table, distance_algorithm)
			images = data_handle.find_similar_images_orange(image_table, distance_matrix, distance_algorithm)
			#cluster = cbir.cluster_images(distance_matrix, image_file_paths, number_of_clusters)

			end_time = time.time()
			seconds = end_time - start_time
			
			data_handle.generate_output_orange(images, query_image_encoded, seconds)
		except Exception as e:
			data_handle.enable_html()
			data_handle.write_into_logs(e)
			print('Something went wrong, ask server administrator to check logs or <b>try using another image </b><br> <a href="../"> Home Page </a>')
		finally:
			data_handle.remove_file_dir(directory)
			data_handle.delete_client(client_id)

cbir_result = Result()
if (cbir_result.cbir_algorithm == 'YOLO'):
	cbir_result.run_cbir_yolo()
else:
	cbir_result.run_cbir_orange()
