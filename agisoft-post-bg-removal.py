"""
*********READ THIS FIRST**************

TO USE THIS CODE ON A NEW COMPUTER:

* open "Run" 
* type "cmd" into the box and press "Ctrl+Shift+Enter" to run as administrator
* cd "%programfiles%\Agisoft\PhotoScan Pro\python"
* python.exe -m pip install numpy
* python.exe -m pip install scipy

if you get an "Access Denied" error while installing the libraries, 
or get an import error in the agisoft console when running this program, 
then this process has not been done correctly


TO RUN:

* open agisoft on an EMPTY PROJECT
* go to toolbar at the top of the screen, and select Tools->Run Script (or type Ctrl+R)
* find this code in your file system (agisoft-automation.py)
* File selection UI will pop up. Select folder which contains folders of photos of sherds
* select folder to save projects to

**************************************

the steps above ensure the correct libraries are imported
these are imported to make dominant-color-finding code work for the removal of the holder/bg.

todo: 
	make a flat 2x2inch metal square for calibration tests
	make it work with his directory system (see slack for example)
	continue the domaninant-color finding code: 
		change the number of clusters, in case we get a big sherd with multiple colors?
		adjust how you calculate the tolerance
		

agisoft automation code
IN PROGRESS
by Jessica Teipel
code used to determine background colors based on the following: https://stackoverflow.com/questions/3241929/python-find-dominant-most-common-color-in-an-image

takes a set of photos, masks them, adds scale bars, and builds the model

""" 

import PhotoScan 
import os
from os import walk
import math
import codecs
import struct

import numpy as np
import scipy
import scipy.misc
import scipy.cluster


def promptForFileLocation():
	dirOfDirs = PhotoScan.app.getExistingDirectory("Choose Directory with folders of photos")
	saveDir = PhotoScan.app.getExistingDirectory("Choose Directory to save projects in")
	dirList = []
	for (dirpath, dirnames, filenames) in walk(dirOfDirs):
		dirList.extend(dirnames)
		break
	return [saveDir, dirOfDirs, dirList]
	
def getPhotosFromDir(photoDir):
	photos = os.listdir(photoDir)
	return photos
	
def importPhotos(photoDir, chunk):
	i = 0 
	while (i < len(photos)):
		photos[i] = str(photoDir + "/" + photos[i])
		i += 1
	
	chunk.addPhotos(photos)

def alignPhotos(chunk):
	for frame in chunk.frames:
		frame.matchPhotos()
	chunk.alignCameras()

def scaling(chunk):
	SCALEBAR_DISTANCE = .03 # 3cm
	chunk.detectMarkers(PhotoScan.TargetType.CrossTarget, 50) # put this back in
	
	markers = chunk.markers

	# for each marker found, find all the markers that are closest to this marker
	# since distances will not be exactly the same, 
	# the "tolerance" value is used to determine if they are "almost" the same distance
	tolerance = .1
	i = 0;
	listOfLists = [[]]*len(markers)
	minDistance = [100000]*len(markers)
	print(listOfLists)
	while i < len(markers):
		j = 0
		while j < len(markers):
			if i != j :
				dist = getDistance(markers[i].position, markers[j].position) 
				if dist < minDistance[i]-minDistance[i]*tolerance:
					minDistance[i] = dist
					(listOfLists[i]) = []
					listOfLists[i].append(j)
				elif dist > minDistance[i]-minDistance[i]*tolerance and dist < minDistance[i]+minDistance[i]*tolerance:
					minDistance[i] = (minDistance[i]*len(listOfLists[i]) + dist)/float((len(listOfLists[i])+1))
					listOfLists[i].append(j)
			j = j+1
		i = i+1
	
	## for debugging:
	#print("list of closest points:")
	#print(listOfLists)
	#print("their distances:")
	#print(minDistance)
	
	# step 1 in ensuring good markers are chosen for the scalebars: 
	# remove any points which are unusually close to or unusually far away from their neighbors
	removablePoints = eliminateOutliers(minDistance)
	#print("bad points: " + str(removablePoints))
	
	# step 2 in ensuring good markers are chosen for the scalebars:
	# get a list of all markers which are not outliers and have EXACTLY four closest neighbors
	i = 0
	goodMarkers = []
	while i < len(listOfLists):
		if i not in removablePoints:
			if len(listOfLists[i]) == 4:
				goodMarkers.append(i)
		i = i+1
	for marker in goodMarkers:
		print(str(marker) + ":" + str(listOfLists[marker]))
		
	# potential step 3?
	# only create a scalebar if both the marker and it's neighbor were classified as good markers in step 2?
	
	# if enough good markers are found after step 2, use these markers
	# if there are not enough, the markers which were considered "good" after step 1 will have to suffice
	if( len(goodMarkers) >= 2):
		for marker in goodMarkers:
			for marker2 in listOfLists[marker]:
				scalebar = chunk.addScalebar(markers[marker], markers[marker2])
				scalebar.Reference.distance = SCALEBAR_DISTANCE
	else:
		marker = 0
		while marker < len(listOfLists):
			if marker not in removablePoints:
				for marker2 in listOfLists[marker]:
					scalebar = chunk.addScalebar(markers[marker], markers[marker2])
					scalebar.Reference.distance = SCALEBAR_DISTANCE
			marker = marker + 1
	
	
	
def sq(x):
	return x*x
	
def getDistance(point1, point2):
	return math.sqrt(sq(point1.x-point2.x) + sq(point1.y-point2.y) + sq(point1.z-point2.z))

def getDistanceColor(array1, array2):
	return math.sqrt(sq(array1[0]-array2[0]) + sq(array1[1]-array2[1]) + sq(array1[2]-array2[2]))
	
def eliminateOutliers(list):
	newList = sorted(list)
	outliers = []
	medianLocation = len(newList)/2
	median = newList[int(medianLocation)]
	Q1MedLoc = len(newList)/4
	Q2MedLoc = 3*len(newList)/4
	Q1Med = newList[int(Q1MedLoc)]
	Q2Med = newList[int(Q2MedLoc)]
	interquartRange = Q2Med - Q1Med
	lowerBound = median - interquartRange*.5#*1.5 #normally multiplied by 1.5, but we want more precision
	upperBound = median + interquartRange*.5#*1.5
	
	i=0
	while i < len(list):
		if list[i] < lowerBound or list[i] > upperBound:
			outliers.append(i)
		i = i+1
	return outliers
	
	
def buildDenseCloud(chunk):
	chunk.buildDepthMaps()
	chunk.buildDenseCloud(PhotoScan.MediumQuality) 	
	

# finds the most common colors in the given photo, and returns them as array of RGB (i.e. [[r,g,b],[r,g,b]...])
def findBGColors(chunk):

	photo = chunk.cameras[0].photo.image()
	
	NUM_CLUSTERS = 4

	img = photo.copy()
	img = img.resize(150, 150)      # optional, to reduce time
	print("resized")
	
	# convert photoscan image object to 2d array of pixels, each with rgb values
	ar = np.fromstring(img.tostring(), dtype=np.uint8)
	ar = ar.reshape(img.height, img.width, img.cn)
	
	# the algorithm that finds most common colors. idk the details
	shape = ar.shape
	ar = ar.reshape(scipy.product(shape[:2]), shape[2]).astype(float)
	print('finding clusters')
	codes, dist = scipy.cluster.vq.kmeans(ar, NUM_CLUSTERS)
	vecs, dist = scipy.cluster.vq.vq(ar, codes)         # assign codes
	counts, bins = scipy.histogram(vecs, len(codes))    # count occurrences
	
	i=0
	sorted_colors = codes.copy()
	sorted_counts = counts.copy()
	while i < NUM_CLUSTERS:
		j=i+1
		while j < NUM_CLUSTERS:
			if sorted_counts[j] > sorted_counts[i]:
				sorted_counts[j], sorted_counts[i] = sorted_counts[i], sorted_counts[j]
				sorted_colors[j], sorted_colors[i] = sorted_colors[i].copy(), sorted_colors[j].copy() 
			j = j+1
		i = i+1
	
	index_max = scipy.argmax(counts)                    # find most frequent, if you want
	
	print('cluster centres:\n', sorted_colors)
	print('num occurences:', sorted_counts)
	
	# return the most common colors
	return sorted_colors
	

# haven't found documentation in agisoft to find the selected points and determine if it's null
# so the try catches are a work around the agisoft error halting the process
# i.e. if no points are found, just move on to the next color
'''
def removeBG(chunk):
	denseCloud = chunk.dense_cloud
	denseCloud.selectPointsByColor([56, 239, 126], 80, 'RGB') # green paint: [R: 56 G: 239 B: 126] 
	try:
		denseCloud.removeSelectedPoints()
	finally:
		denseCloud.selectPointsByColor([53, 59, 47], 50, 'RGB') #black
		try:
			denseCloud.removeSelectedPoints()
		finally: 
			denseCloud.selectPointsByColor([231, 234, 239], 15, 'RGB') #white
			try: 
				denseCloud.removeSelectedPoints()
			finally:
				denseCloud.selectPointsByColor([4, 62, 12], 80, 'RGB') # darker green
				try:
					denseCloud.removeSelectedPoints()
				finally:
					return
	"""
	## another option???
	# denseCloud.selectMaskedPoints(cameras, softness=4)
	# denseCloud.removeSelectedPoints([pointClass])
	"""
'''

def removeBG(chunk, colors):

	white = [255,255,255]
	black = [0,0,0]
	#green = [0, 255, 0]
	
	removeBGColor(chunk, colors, white)
	removeBGColor(chunk, colors, black)
	#removeBGColor(chunk, colors, green)
	

def removeBGColor(chunk, colors, ideal):

	denseCloud = chunk.dense_cloud

	closestToIdeal, distance = getClosestColor(colors, ideal)
	denseCloud.selectPointsByColor(ideal, int(.5*(distance)))
	try:
		denseCloud.removeSelectedPoints()
	finally:
		return;
		#closestToActualColor, tolerance = getClosestColor(colors, colors[closestToIdeal])
		#denseCloud.selectPointsByColor(colors[closestToIdeal], int(tolerance**(1./3)))# todo: find way to better calculate tolerance))
		#try:
			#denseCloud.removeSelectedPoints()
		#finally: 
		#	return

def getClosestColor(colors, ideal):
	closestToIdeal = 0
	distance = float('inf')
	i=0
	while i< len(colors):
		colorDistance = getDistanceColor(colors[i], ideal)
		if colorDistance < distance and colorDistance != 0:
			closestToIdeal = i
			distance = colorDistance
		i = i+1
	return closestToIdeal, distance
	
def buildModel(chunk):
	chunk.buildModel(surface=PhotoScan.Arbitrary, interpolation=PhotoScan.EnabledInterpolation) 

def buildTexture(chunk):
	chunk.buildUV()
	chunk.buildTexture()
	

# main workflow. 
# I have created functions so that each step in the manual process is a single function call here

#[saveDir, dirOfDirs, dirList] = promptForFileLocation()

#colors = findBGColors(PhotoScan.app.document.chunk)
#removeBG(PhotoScan.app.document.chunk, colors)
#scaling(PhotoScan.app.document.chunk)

#i = 0;
#while(i < len(dirList)):
	#photoDir = dirOfDirs + "/" + dirList[i]
	#photos = getPhotosFromDir(photoDir)

doc = PhotoScan.app.document
# a work around to make a "new" document
#doc.clear()
#chunk = doc.addChunk()
chunk = doc.chunk

"""
importPhotos(photoDir, chunk)
alignPhotos(chunk)
buildDenseCloud(chunk)
scaling(chunk)
findBGColors(photoDir + "/" + photos[0])
colors = findBGColors(PhotoScan.app.document.chunk)
removeBG(PhotoScan.app.document.chunk, colors)
"""

buildModel(chunk)
buildTexture(chunk)
	#removeLighting(color_mode=SingleColor, internal_blur=1.0, mesh_noise_suppression=1.5, ambient_occlusion_path=’‘, ambient_occlusion_multiplier=1.0[, progress])
	#doc.save(saveDir + "/" + dirList[i] + ".psx")
	#i = i+1
#PhotoScan.app.quit()

