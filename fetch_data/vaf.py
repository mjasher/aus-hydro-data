"""
========================================================
Victorian aquifer framework (ftp://ftp1.land.vic.gov.au/VAF/)


michael.james.asher@gmail.com
November 2015
========================================================

"""

import subprocess
import os
from PIL import Image
import numpy
import matplotlib.pylab as plt


files = [
			"bse_1t",
			"cps_1t",
			"cps_2b",
			"lmta_1t",
			"lmta_2b",
			"lmtd_1t",
			"lmtd_2b",
			"lta_1t",
			"lta_2b",
			"ltba_1t",
			"ltba_2b",
			"ltbb_1t",
			"ltbb_2b",
			"qa_1t",
			"qa_2b",
			"sur_1t",
			"umta_1t",
			"umta_2b",
			"umtd_1t",
			"umtd_2b",
			"utaf_1t",
			"utaf_2b",
			"utam_1t",
			"utam_2b",
			"utb_1t",
			"utb_2b",
			"utd_1t",
			"utd_2b",
			"utqa_1t",
			"utqa_2b",
			"utqd_1t",
			"utqd_2b"
			]

def run(bounding_box, destination_dir):
	base_dir = "../downloaded_data/ESRI_GRID/"
	for f in files:
		print str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
		file_name = os.path.join(base_dir, f)
		tif_name = os.path.join(destination_dir, f+'.tif')
		subprocess.call([
			"gdalwarp",
			# <x_min> <y_min> <x_max> <y_max> 
			"-te", str(bounding_box[0][1]), str(bounding_box[1][0]), str(bounding_box[1][1]), str(bounding_box[0][0]),
			"-t_srs", "EPSG:4326", 
			file_name, tif_name, 
			])

		im = Image.open(tif_name)
		# # im.show()
		arr = numpy.array(im)
		arr[arr < -1e+38] = 0
		if numpy.max(arr) == numpy.min(arr):
			os.remove(tif_name)

def plot(destination_dir):
	for f in files:
		tif_name = os.path.join(destination_dir, f+'.tif')
		try:
			im = Image.open(tif_name)
			# # im.show()
			arr = numpy.array(im)
			arr[arr < -1e+38] = 0
			# print numpy.min(arr)
			# print numpy.max(arr)
			plt.imshow(arr)
			plt.colorbar()
				# print arr
			plt.show()		
		except:
			pass
		# subprocess.call([
		# 	"ogr2ogr",
		# 	"-clipsrc", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
		# 	"-f", "GeoJSON", 
		# 	os.path.join(destination_dir,f+'.json'), os.path.join(destination_dir, f+'.tif'),
		# 	"-t_srs", "EPSG:4326", 
		# 	])


if __name__ == '__main__':
	bounding_box = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
	destination_dir = "../clipped_data/vaf"
	# run(bounding_box, destination_dir)
	plot(destination_dir)