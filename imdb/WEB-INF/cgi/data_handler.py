from packages import *
from layout import Layout

class DataHandler(Layout):
	# class to perform all operations related to data such as file transfer, database operations, file processing etc.
	__database = None
	__mongo = None
	__lab = False

	def __init__(self):
		pass

	def __init__(self, database, lab = False, username=None, password=None):
		self.__database = database #database containing images
		self.__mongo = DatabaseMongoDB()	#object of Database MongoDB class
		if(username == None and password == None):
			# initialize database without authentication
			self.__mongo.initialize('localhost', self.__database)
		else:
			# initialize database with authentication
			self.__mongo.initialize('localhost', self.__database, username=username, password=password)
		self.__mongo.initialize_gridFS()
		self.__lab = lab

	def process_annotation_file(self, annotation_file, directory):
		'''
		process text file containing annotations
		input => 	annotation_file-> 		text file received from client in cgi
					directory -> 			directory containing images and annotations
		output=>	save annotation file on web server
		'''
		directory += '/'
		fn = os.path.splitext(annotation_file.filename)[0]
		open(directory + fn + '.txt', "wb").write(annotation_file.file.read())

	def process_image_file(self, directory, image_file, query = False):
		'''
		process image file
		input => 	image_file-> 			image received from client in cgi
					directory -> 			directory containing images and annotations
					query->					True, if image is query image (required for lab)
		output=>	return encoded_string->	base64 encooded string of image
		'''
		directory += '/'
		fn = os.path.splitext(image_file.filename)[0]
		if(query):
			fn = 'query'
		open(directory + fn + ".png", "wb").write(image_file.file.read())
		current_img = Image.open(directory + fn + ".png")
		current_img.save(directory + fn + '.png', 'PNG')

		with open(directory + fn + '.png', "rb") as image_file:
			encoded_string = base64.b64encode(image_file.read())

		return encoded_string

	def __filename_exists_in_database(self, filename):
		'''
		check if file with same name exists in database
		input => 	filename-> 		filename 
		output=>	return True->	if file exists
						   False->	if file does not exist
		'''
		if(self.__mongo.get_file_gridFS(filename) == None):
			return False
		
		return True

	def __same_image_exists_in_database(self, image_with_path):
		'''
		check if same image exists in database
		input => 	image_with_path-> 	image file with path 
		output=>	return True, result->	if file exists, return file details
						   False->			if file does not exist, return None
		'''
		md5_hash = hashlib.md5()
		image_file = open(image_with_path, "rb")
		image = image_file.read()
		md5_hash.update(image)
		digest = md5_hash.hexdigest()
		result = self.__mongo.find_one('fs.files', {'md5':digest})
		if(result == None):
			return False, None

		return True, result

	def __image_exists_in_database(self, directory, filename):
		'''
		check if image exists in database
		input => 	filename-> 		filename 
					directory->		directory containing images
		output=>	return 0->	if same filename exists in database (not for lab)
						   1->	if same image exists in database
						   2-> 	if image does not exist in database
						   3->	if same filename exists in database (for lab)
		'''
		directory += '/'
		feedback = []
		
		flag, data = self.__same_image_exists_in_database(directory + filename)
		if(flag):
			return 1
		else:
			if(self.__filename_exists_in_database(filename) and self.__lab == False):
				return 0
			elif(self.__filename_exists_in_database(filename) and self.__lab == True):
				return 3

			return 2

	def rename_files(self, directory, filename):
		'''
		rename image files
		input => 	filename-> 				current filename 
					directory->				directory containing images
		output=>	return new_filename->	new name of file	
	   '''
		new_filename = os.path.splitext(filename)[0] + str(random.randint(1,1000))
		if(self.__filename_exists_in_database(new_filename + '.png')):
			new_filename = self.rename_files(directory, new_filename)
		
		os.rename(directory + filename, directory + new_filename + '.png')
		os.rename(directory + os.path.splitext(filename)[0] + '.txt', directory + new_filename + '.txt')
		return new_filename

	def save_images_to_database(self, directory = '../../temp_files'):
		'''
		save images to database
		input => 	directory->		directory containing images (only if different default)
		output=>	return feedback->	image details if image is saved to database
	   '''
		directory += '/'
		feedback = {}
		for filename in os.listdir(directory):
			if filename.endswith(".png"):
				flag =self.__image_exists_in_database(directory, filename)
				if(flag == 1 or flag == 3):
					if(self.__lab == False):
						print('<br>File <b>' + filename + '</b> already exists in database.')
					else:
						feedback[filename] = None
				else:
					if(flag == 0):
						filename = self.rename_files(directory, filename)
					elif(flag == 2):
						iid = self.__mongo.put_file_gridFS(os.path.join(directory, filename))
						#manual hash
						md5_hash = hashlib.md5()
						image_file = open(directory + filename, "rb")
						image = image_file.read()
						md5_hash.update(image)
						digest = md5_hash.hexdigest()
						self.__mongo.update_one('fs.files',{'_id':iid}, {"$set":{'md5':digest}})
						if(self.__lab == False):
							print('<br>Image ' + filename + ' inserted into database.')
						else:
							#feedback['msg'].append('<br>Image ' + filename + ' inserted into database.')
							feedback[filename] = self.__mongo.find_one('fs.files',{'_id':iid})
		return feedback

					

	def save_features_to_database(self, image_table, embeddings, image_embedder, directory = '../../temp_files'):
		'''
		save features extracted using orange to database
		input => 	image_table->		image table created using Orange (or csv)
					embeddings->		feature vectors of all images
					image_emebedder->	feature extraction algorithm by orange
					directory ->		directory containing images (only if different default)
		output=>	return feedback->	image details after features are saved to database
	   '''
		feedback = {}
		directory += '/'
		for i in range(len(image_table)):
			flag, data = self.__same_image_exists_in_database(directory + str(image_table[i]['image']))
			if(flag):
				myquery = {"filename": str(data['filename'])}
				newvalues = { "$set": { "metadata." + image_embedder: embeddings[i]} }
				self.__mongo.update_one("fs.files", myquery, newvalues)
				if(self.__lab == False):
						print('<br>Features of <b>' + str(image_table[i]['image']) + '->' + str(data['filename']) + '</b> (' + image_embedder + ')inserted into database.')
				else:
					feedback[str(data['filename'])] = self.__mongo.find_one('fs.files', myquery)
					#feedback.append('<br>Features of <b>' + str(image_table[i]['image']) + '->' + str(data['filename']) + '</b> (' + image_embedder + ')inserted into database.')

		return feedback

	def save_annotations_to_database(self, image_table, directory = '../../temp_files'):
		'''
		save annotations to database
		input => 	image_table->		image table created using Orange (or csv
					directory->			directory containing images (only if different default)
		output=>	return feedback->	annotations are saved to database
	   '''
		feedback = []
		directory +='/'
		for i in range(len(image_table)):
			flag, data = self.__same_image_exists_in_database(directory + str(image_table[i]['image']))
			if(flag):
				myquery = {"filename": str(data['filename'])}
				file = open(directory + str(image_table[i]['image name']) + ".txt", "r")
				annotations = file.read()
				newvalues = { "$set": { "metadata.annotations" : annotations} }
				self.__mongo.update_one("fs.files", myquery, newvalues)
				if(self.__lab == False):
						print('<br>Annotations of <b>' + str(image_table[i]['image']) + '->' + str(data['filename']) + '</b> inserted into database.')
				else:
					feedback.append('<br>Annotations <b>' + str(image_table[i]['image']) + '->' + str(data['filename']) + '</b> inserted into database.')

		return feedback

	def remove_files(self, directory):
		for f in os.listdir(directory):
			os.remove(os.path.join(directory, f))

	def remove_file(self, filename, directory):
		os.remove(os.path.join(directory, filename))
		if(self.__lab == False):
			os.remove(os.path.join(directory, os.path.splitext(filename)[0] + '.txt'))

	def remove_file_dir(self, directory):
		for f in os.listdir(directory):
			os.remove(os.path.join(directory, f))
		os.rmdir(directory)

	def upadte_csv(self, image_table, directory = '../../'):
		'''
		add entry of new image to csv file
		input=>		image_table->		image table created using Orange (or csv)
					directory ->		directory containing images (only if different default)
		output=>	updated csv
	   '''
		with open(directory + self.__database + '.csv', 'r') as inp, open(directory + self.__database + '_edit.csv', 'w', newline='') as out:
			writer = csv.writer(out)
			images = []
			for row in csv.reader(inp):
				images.append(row[0])
				if row[0] != "zzzzzzz":
					writer.writerow(row)

			for i in range(len(image_table)):
				flag = False
				for j in range(len(images)):
					if(str(images[j]) == str(image_table[i]['image name'])):
						flag = True
						break
				if(self.__mongo.get_file_gridFS(str(image_table[i]['image'])) == None and flag == False):
					writer.writerow([str(image_table[i]['image name']),str(image_table[i]['image']), str(image_table[i]['size']),str(image_table[i]['width']),str(image_table[i]['height'])])

			writer.writerow(['zzzzzzz','zzzzzzz.png', 55072,171,182])

		os.remove(directory + self.__database + '.csv')
		os.rename(directory + self.__database + '_edit.csv', directory + self.__database + '.csv')

	def get_features_from_database(self, image_table, algorithm):
		'''
		retrieve features saved in database
		input => 	image_table->		image table created using Orange (or csv)
					algorithm ->		feature extraction algorithm
		output=>	return embeddings->	feature vectors of images in database
	   '''
		embeddings = [None] * (len(image_table))
		for i in range(len(image_table) - 1):
			mydoc = self.__mongo.find("fs.files",{"filename":str(image_table[i,'image'])})
			for x in mydoc:
				embeddings[i] = x["metadata"][algorithm]

		return embeddings

	def return_images_lab_binary(self, cluster = None, image_list = None):
		'''
		get base64 encoding of images 
		input => 	cluster->			object labels detected from images
					image_list->		list of images
		output=>	return images_binary->	base64 ecnodings of provided imges
	   '''
		images_binary = {}
		encoded_string = None
		if(cluster != None):
			for x in cluster:
				filename = os.path.basename(x)
				if('zzzzzzz.png' == filename):
					pass
				else:
					out = self.__mongo.get_file_gridFS(filename)
					encoded_string = 'data:image/png;base64,' + base64.b64encode(out.read()).decode('utf-8')
					images_binary.append(encoded_string)

		elif (image_list != None):
			for x in image_list:
				filename = os.path.basename(x)#['filename'])
				images_binary[filename] = []
				out = self.__mongo.get_file_gridFS(filename)
				encoded_string = 'data:image/png;base64,' + base64.b64encode(out.read()).decode('utf-8')
				images_binary[filename].append(str(encoded_string))


		return images_binary

	def return_images_lab_json(self, image_table):
		'''
		get image details in json format
		input => 	image_table->		image table created using Orange (or csv)
		output=>	return feedback->	image details in json format
	   '''
		feedback = {}
		for i in range(len(image_table) - 1):
			feedback[str(image_table[i,'image'])] = self.__mongo.find_one('fs.files',{'filename':str(image_table[i,'image'])})


		return feedback

	def generate_output_orange(self, cluster, current_img, seconds):
		'''
		generate output for Orange (for Search Engine)
		input => 	cluster->			cluster containing similar images
					current_img->		query image base64 encoded
					seconds-> 			time elapsed
		output=>	display images in cluster
	   '''
		self.enable_html()
		self.draw_header()
		print('         <div>')
		print('             <h4>Query Image:<span id="imgName"></span></h4><br>')
		print('             <br> <img id="Img123" src=\'data:image/png;base64,' + str(current_img.decode('utf-8')) + '\' height="100px" width="100px">')
		print('             <h4>' +str(len(cluster) - 1) + ' image(s) in '+ str(round(seconds, 4)) +' second(s) <a href="../index.html">Back to Search</a></h4>')
		print('         </div>')
		print('         <div id="result" class=" scrollbar">')
		#retrieving the filenames from identified cluster and displaying them with annotations
		for x in cluster:
			filename = os.path.basename(cluster[x]['image'])
			similarity = round(cluster[x]['similarity'], 2)
			if('zzzzzzz.png' == filename):
				pass
			else:
				out = self.__mongo.get_file_gridFS(filename)
				encoded_string = base64.b64encode(out.read())
				myDesc =""
				myDesc1 = self.__mongo.find_one('fs.files', {"filename": filename})['metadata']['annotations']
				myDesc = str(myDesc1)
				myDesc = myDesc.replace('#', '')
				myDesc = myDesc.replace('\"', '')
				myDesc = re.sub('\d','',myDesc)
				myDesc = myDesc.replace('metadata','')
				myDesc = myDesc.replace('annotations','')
				myDesc = myDesc.replace('{','')
				myDesc = myDesc.replace('}','')
				print('<div style="display:inline-block; ">')#overflow-y: auto;
				print('<figure class="figure">')
				print('     <img src=\'data:image/png;base64,' + str(encoded_string.decode('utf-8')) + '\' height="200px" width="200px">')
				print('		<figcaption class="figcaption"><b>Similarity:</b>' + str(similarity) + '%<br></figcaption>')
				print('</figure>')
				print('</div>')
		print('         </div>')
		self.draw_footer()

	def generate_output_tbir(self, search_term):
		'''
		generate output for TBIR (for Search Engine)
		input => 	search term->		query keyword
		output=>	display images based on keyword
	   '''
		start_time = time.time()
		myquery = {"$text": {"$search": search_term}}
		images = self.__mongo.find("fs.files", myquery)
		end_time = time.time()
		seconds = end_time - start_time 

		self.enable_html()
		self.draw_header()
		print('<div class=""> ')
		
		print('<h4>' + str(images.count()) + ' results for ' + search_term + ' in ' + str(round(seconds, 4)) + ' seconds <a href="../index.html">Back to Search</a></h4>')
		print('</div>')

		print('<div id="result" class=" scrollbar" style="height:450px">')
		#displaying the images which contains the searched keyword
		for x in images:
			filename = os.path.basename(x["filename"])
			out = self.__mongo.get_file_gridFS(filename)
			encoded_string = base64.b64encode(out.read())
			print('<img src=\'data:image/png;base64,' + str(encoded_string.decode('utf-8')) + '\' height="150px" width="150px">')
		print('</div>')
		self.draw_footer()

	def create_random_client(self):
		'''
		create rndom clients based on request to server
		input => 	
		output=>	return client_id-> id of client
	   '''
		client_id = random.randint(1,100000)
		query = {"client_id":client_id}
		cid = self.__mongo.find_one("file_up", query)
		if(cid == client_id):
			create_random_client()

		self.__mongo.insert('file_up', {'client_id':client_id})
		return client_id

	def delete_client(self, client_id):
		self.__mongo.delete('file_up', {'client_id':client_id})

	def find_similar_images_orange(self, image_table, distance_matrix, distance_algo):
		'''
		find similar images using Orange
		input => 	image_table->		image table created using Orange (or csv)
					distance_matrix->	distance_matrix
					distance_algo-> 	distance algorithm in Orange
		output=>	return image_list->	return image list with distance and similarity percentage
	   '''
		i = len(image_table) - 1
		enumerate_object = enumerate(distance_matrix[i])
		sorted_pairs = sorted(enumerate_object, key=operator.itemgetter(1))
		maxDist = np.amax(distance_matrix)
		minDist = 0
		sim = 50
		if(distance_algo == 'Cosine'):
			maxDist = 1
			sim = 70


		distSet = set(distance_matrix[i])
		if(self.__lab == False):
			maxDist2 = np.amax(distance_matrix[i])
			minDist = sorted(distSet)[1]
			myRange = maxDist2 - minDist
		
		image_list = {}

		for i in range(len(sorted_pairs)):
			img = str(image_table[sorted_pairs[i][0],'image'])
			dist_current = sorted_pairs[i][1]
			dist_percent = 0
			similarity_current = 0
			dist_current_percent = 0#(dist_current / maxDist) * 100
			if(self.__lab == False):
				dist_current_percent = (dist_current / maxDist) * 100
				dist_current_percentage = (dist_current / myRange) * 100
			else:
				dist_current_percentage = (dist_current / maxDist) * 100

			similarity_current = 100 - dist_current_percentage
			similarity_a = 100 - dist_current_percent
			if(similarity_current > 0):
				if(self.__lab == False):
					if(similarity_a >= sim):
						image_list[img] = {}
						image_list[img]['image'] = img
						image_list[img]['distance'] = dist_current
						image_list[img]['distance_percentage'] = dist_current_percentage
						image_list[img]['similarity'] = similarity_a
				else:
					image_list[img] = {}
					image_list[img]['image'] = img
					image_list[img]['distance'] = dist_current
					image_list[img]['distance_percentage'] = dist_current_percentage
					image_list[img]['similarity'] = similarity_current


		return image_list


	def validate_login(self, username, password):
		login = self.__mongo.find_one('login',{'username':username,'password':password})
		return login

	def write_into_logs(self, exception):
		current_time = time.time()
		current_time = datetime.datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M:%S')
		file = open('../../logs/logs.txt', "a")
		file.write(current_time + " | " + str(exception) + "\n")

	def create_text_index(self, collection, field):
		self.__mongo.create_text_index(collection, field)

