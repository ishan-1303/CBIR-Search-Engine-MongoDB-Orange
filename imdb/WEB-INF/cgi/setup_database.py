from packages import *
from cbir import CBIR
from data_handler import DataHandler

def read_arguments():
	ap = argparse.ArgumentParser()
	ap.add_argument("-image_path", "--path", required=True,
			help="path to images files")
	ap.add_argument("-database", "--db", required=True,
			help="database name")
	args = vars(ap.parse_args())
	return args

def process_images(path_to_images):
	path_to_images += '/'
	for f in os.listdir(path_to_images):
		if(os.path.splitext(f)[1] != '.txt'):
			fn = os.path.splitext(f)[0]
			current_img = Image.open(path_to_images + f)
			current_img.save(path_to_images + fn + '.png', 'PNG')

def create_csv(db):
	import csv
	with open(db + '.csv', 'r') as inp, open(db + '_edit.csv', 'w', newline='') as out:
		writer = csv.writer(out)
		for row in csv.reader(inp):
			writer.writerow(row)
			
		writer.writerow(['zzzzzzz','zzzzzzz.png', 55072,171,182])

	os.remove(db + '.csv')
	os.rename(db + '_edit.csv', db + '.csv')

def initialize():
	#complete installation
	setup_spec = read_arguments()
	db = setup_spec['db']
	directory = setup_spec['path']

	#process_images(directory)

	cbir = CBIR(db)

	data_handle = DataHandler(db, lab = False, username=None, password=None)

	print('\nuploading images to database')
	data_handle.save_images_to_database(directory)

	print('\ncreating image table')
	image_table = cbir.create_image_table(directory)
	image_table.save('../../' + db + ".csv")
	create_csv('../../' + db)	

	print('\nextracting features-inception-v3')
	features_inceptionv3 = cbir.extract_features_from_images('inception-v3', image_table, directory)

	print('\nsaving features-inception-v3 to database')
	data_handle.save_features_to_database(image_table, features_inceptionv3, 'inception-v3', directory)

	print('\nextracting features-vgg16')
	features_vgg16 = cbir.extract_features_from_images('vgg16', image_table, directory)

	print('\nsaving features-vgg16 to database')
	data_handle.save_features_to_database(image_table, features_vgg16, 'vgg16', directory)

	print('\nextracting features-vgg19')
	features_vgg19 = cbir.extract_features_from_images('vgg19', image_table, directory)

	print('\nsaving features-vgg19 to database')
	data_handle.save_features_to_database(image_table, features_vgg19, 'vgg19', directory)

	print('\nuploading annotations to database')
	data_handle.save_annotations_to_database(image_table, directory)


initialize()

#how to run
#open orange command prompt and run the below line by changing image path (please do not change database name)
#python setup_database.py -image_path C:\Users\ishan\OneDrive\CME-IMP\Thesis\domestic-animals -database imagedb
					