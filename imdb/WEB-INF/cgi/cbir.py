from packages import *

class CBIR():
	# this class provides methods to perform Content Based Image Retrieval

	__database = None
	__image_table = None
	__yolo = None
	__weightsPath = None
	__configPath = None

	def __init__(self, database):
		self.__database = database 		# database which stores images
		self.__yolo = 'yolo-coco' 		# folder containing yolo files
		self.__weightsPath = self.__yolo + '/' + 'yolov3.weights' 
		self.__configPath = self.__yolo + '/' +'yolov3.cfg'

	def create_image_table(self, directory):
		'''
		import images from directory and create data table of images using ImportImages class of Orange
		input => 	directory -> 			directory containing images
		output=>	returns image table -> 	image table of images
		'''
		import_images = ImportImages()
		data, err = import_images(directory)
		self.__image_table = data

		return self.__image_table

	def create_image_table_from_csv(self, directory = '../..'):
		'''
		create imge table from csv file
		input => 	directory -> 			directory if different from root folder of project
		output=>	returns image table -> 	image table of images
		'''
		directory += '/'
		self.__image_table = Table.from_file(directory + self.__database + '.csv')

		return self.__image_table

	def get_image_file_paths(self, directory):
		'''
		create list of image file paths
		input => 	directory -> 				directory containing images
		output=>	returns image_file_paths-> 	list of complete image paths
		'''
		image_file_paths = [None] * len(self.__image_table)
		for i in range(len(self.__image_table)):
		    image_file_paths[i] = directory + "/" +  str(self.__image_table[i]['image'])

		return image_file_paths

	def extract_features_from_images(self, image_embedder, query_image_table, directory):
		'''
		extract features from images
		input => 	image_embedder -> 			feature extraction algorithm provided by Orange
					query_image_table -> 		image table o query image or all images
					directory -> 				directory containing images
		output=>	returns embeddings-> 		feature vector of all images
		'''
		embeddings = [None] * (len(query_image_table))
		image_file_paths = self.get_image_file_paths(directory)
		with ImageEmbedder(model = image_embedder) as emb:
			embeddings = emb(image_file_paths)

		return embeddings

	def prepare_embedding_table(self, embeddings, embeddings_query_image):
		'''
		create taable of image features
		input => 	embeddings -> 					feature vector of all images from database
					embeddings_query_image -> 		feature vector of query image
		output=>	returns image_embedder_table-> 	combined table of feature vectors of query image and all images from database
		'''
		embeddings[len(self.__image_table) -1] = embeddings_query_image[0]
		image_embedder_table = ImageEmbedder.prepare_output_data(self.__image_table, embeddings) 
		return image_embedder_table

	def compute_distance(self, image_embedder_table, distance_algorithm):
		'''
		create taable of image features
		input => 	image_embedder_table -> 	combined table of feature vectors of query image and all images from database
					distance_algorithm -> 		distance algorithm provided by Orange (Cosine or Euclidean)
		output=>	returns dist_matrix-> 		distance matrix
		'''
		dist = image_embedder_table[0]
		if(distance_algorithm == 'Cosine'):
			dist_matrix = Cosine(dist)
		else:
			dist_matrix = Euclidean(dist)

		return dist_matrix

	def cluster_images(self, dist_matrix, image_file_paths, number_of_clusters):
		'''
		perform hierarchical clustering 
		input => 	dist_matrix -> 		 		distance matrix
					image_file_paths -> 		list of complete image paths
					number_of_clusters->		number of clusters (at least 2)
		output=>	returns groups[cluster]-> 	cluster containing similar images
		'''
		groups = {}
		hierar = hierarchical.HierarchicalClustering(n_clusters = number_of_clusters)
		hierar.linkage = hierarchical.WARD
		hierar.fit(dist_matrix)
		#print(image_file_paths)
		for file, cluster in zip(image_file_paths, hierar.labels):
			if cluster not in groups.keys():
				groups[cluster] = []
				groups[cluster].append(file)
			else:
				groups[cluster].append(file)

		#to find out in which cluster the uploaded image went
		cluster = 0
		c = 0
		for x in groups:
			for y in groups[x]:
				c = c + 1
				fi = os.path.basename(image_file_paths[len(image_file_paths) - 1])
				fy = os.path.basename(y)
				if(fi == fy):
					cluster = x #cluster to be chosen 
					break
		return groups[cluster]

	def load_yolo(self):
		'''
		load yolo object detection model(yolov3)
		'''
		labelsPath = os.path.sep.join([self.__yolo, "coco.names"])
		LABELS = open(labelsPath).read().strip().split("\n")
		np.random.seed(42)
		COLORS = np.random.randint(0, 255, size=(len(LABELS), 3),
			dtype="uint8")

		net = cv2.dnn.readNetFromDarknet(self.__configPath, self.__weightsPath)
		return net, LABELS, COLORS

	def detect_objects_from_image(self, similarity_confidence, image_file):
		'''
		perform object detection on image
		input => 	similarity_confidence -> 		probability of object detection (0.25 is preferred)
					image_file -> 					image file
		output=>	returns object_labels-> 		object labels with probability
		'''
		net, LABELS, COLORS = self.load_yolo()
		image = image_file
		image = cv2.imread(image)
		(H, W) = image.shape[:2]
		ln = net.getLayerNames()
		ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]
		blob = cv2.dnn.blobFromImage(image, 1 / 255.0, (416, 416),
			swapRB=True, crop=False)
		net.setInput(blob)
		start = time.time()
		layerOutputs = net.forward(ln)
		end = time.time()
		boxes = []
		confidences = []
		classIDs = []

		for output in layerOutputs:
			for detection in output:
				scores = detection[5:]
				classID = np.argmax(scores)
				confidence = scores[classID]
				if confidence > similarity_confidence:
					box = detection[0:4] * np.array([W, H, W, H])
					(centerX, centerY, width, height) = box.astype("int")
					x = int(centerX - (width / 2))
					y = int(centerY - (height / 2))
					boxes.append([x, y, int(width), int(height)])
					confidences.append(float(confidence))
					classIDs.append(classID)

		idxs = cv2.dnn.NMSBoxes(boxes, confidences, similarity_confidence,
			0.3)

		object_labels = {}
		if len(idxs) > 0:
			for i in idxs.flatten():
				(x, y) = (boxes[i][0], boxes[i][1])
				(w, h) = (boxes[i][2], boxes[i][3])
				color = [int(c) for c in COLORS[classIDs[i]]]
				cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)
				text = "{}: {:.4f}".format(LABELS[classIDs[i]], confidences[i])
				cv2.putText(image, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX,
					0.5, color, 2)
				object_labels[LABELS[classIDs[i]]] = confidences[i]
		return object_labels


	
