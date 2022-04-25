from packages import *
from input_handler import InputHandler
from cbir import CBIR
from data_handler import DataHandler

class Admin:
	def __init__(self):
		
		ui = InputHandler()
		database, files, username, password = ui.get_user_input_admin()

		d_h = DataHandler('login')
		login = d_h.validate_login(username, password)
		d_h.enable_html()
		d_h.draw_header()
		if login != None:
			cbir = CBIR(database)
			data_handle = DataHandler(database, lab = False, username=None, password=None)
			
			directory = '../../temp_files' 
			for fileitem in files:
				if fileitem.filename:
					if os.path.splitext(fileitem.filename)[1] == '.png' or os.path.splitext(fileitem.filename)[1] == '.jpg' or os.path.splitext(fileitem.filename)[1] == '.jpeg':
						data_handle.process_image_file(directory, fileitem)
					elif os.path.splitext(fileitem.filename)[1] == '.txt':
						data_handle.process_annotation_file(fileitem, directory)


			
			data_handle.save_images_to_database()
			image_table = cbir.create_image_table(directory)
			if(image_table != None):
				embeddings_inceptionv3 = cbir.extract_features_from_images('inception-v3', image_table, directory)
				embeddings_vgg16 = cbir.extract_features_from_images('vgg16', image_table, directory)
				embeddings_vgg19 = cbir.extract_features_from_images('vgg19', image_table, directory)

				data_handle.upadte_csv(image_table)
				data_handle.save_features_to_database(image_table, embeddings_inceptionv3, 'inception-v3')
				data_handle.save_features_to_database(image_table, embeddings_vgg16, 'vgg16')
				data_handle.save_features_to_database(image_table, embeddings_vgg19, 'vgg19')
				data_handle.save_annotations_to_database(image_table)

				data_handle.remove_files(directory)
			else:
				print('No operation performed')

			print('<a href="../Admin Login/"> Add more images </a>')
		else:
			print('    <meta http-equiv="refresh" content="0;url='+str('../Admin Login/')+'" />')

		d_h.draw_footer()

admin = Admin()