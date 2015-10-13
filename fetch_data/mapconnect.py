import os
import subprocess

"""
========================================================
Convert Mapconnect shapefiles to geojson
Shapefiles downloaded from [Mapconnect](http://mapconnect.ga.gov.au/MapConnect/250K/)

michael.james.asher@gmail.com
October 2015
========================================================
"""


def run(bounding_box, destination_dir):
	for file_name in [
					"downloaded_data/FME_b00880673163117/APPT250K_WatercourseLines_line.shp", 
					"downloaded_data/FME_b00880673163117/APPT250K_Contours_line.shp",
					"downloaded_data/FME_b00880673163117/APPT250K_NativeVegetationAreas_poly.shp",
					"downloaded_data/FME_b00880673163117/APPT250K_CultivatedAreas_poly.shp",
					"downloaded_data/FME_b00880673163117/APPT250K_Sands_poly.shp",
					]:
		subprocess.call([
			"ogr2ogr",
			"-clipsrc", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
			"-f", "GeoJSON", os.path.join(destination_dir,os.path.basename(file_name).replace(".shp",".json")), file_name,
			"-t_srs", "EPSG:4326" 
			])