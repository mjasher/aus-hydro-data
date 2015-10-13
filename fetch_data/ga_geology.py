"""
========================================================
Geology data from  GA [Surface Geology of Australia 1:1 million scale dataset 2012 edition](http://www.ga.gov.au/metadata-gateway/metadata/record/gcat_c8856c41-0d5b-2b1d-e044-00144fdd4fa6/Surface+Geology+of+Australia+1%3A1+million+scale+dataset+2012+edition) by downloading the [shapefile](http://www.ga.gov.au/corporate_data/74619/74619_1M_shapefiles.zip).
Faults ShearDisplacementLines1M, GeologicUnitPolygons1M.


michael.james.asher@gmail.com
October 2015
========================================================
"""

import subprocess
import os

def run(bounding_box, destination_dir):
	file_name = "downloaded_data/shapefiles/ShearDisplacementLines1M.shp"
	subprocess.call([
		"ogr2ogr",
		"-clipsrc", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
		"-f", "GeoJSON", os.path.join(destination_dir,os.path.basename(file_name).replace(".shp",".json")), file_name,
		"-t_srs", "EPSG:4326" 
		])