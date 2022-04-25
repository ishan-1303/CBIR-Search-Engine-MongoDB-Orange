# all required packages
from pymongo import MongoClient 
import gridfs
import os
import numpy as np
import Orange
from orangecontrib.imageanalytics.import_images import ImportImages
from orangecontrib.imageanalytics.image_embedder import ImageEmbedder
from Orange.distance import Cosine, Euclidean
from Orange.clustering import hierarchical
import re
from database_mongodb import DatabaseMongoDB
from Orange.data import Table
from timeit import default_timer as timer
import cgi
import cgitb; cgitb.enable()
from PIL import Image
from PIL import UnidentifiedImageError
import random
import base64
from shutil import copyfile
import csv
import time
import math
import cv2
import datetime
import argparse
import hashlib
import sys
import json
import cgi
from pathlib import Path
import operator
