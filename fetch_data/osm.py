import os
import subprocess

"""
========================================================
Converts OSM XML to shp or geojson.

Download OSM XML (map.osm) from
http://www.openstreetmap.org/export#map=9/-36.1412/144.9564


michael.james.asher@gmail.com
October 2015
========================================================
"""

bounding_box = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
download_dir = "/home/mikey/Desktop/aus-hydro-data/downloaded_data/"
clipped_dir = "/home/mikey/Desktop/aus-hydro-data/clipped_data/"
file_name = "/home/mikey/Downloads/map.osm"

def make_shp():
	subprocess.call([
			"ogr2ogr",
			"-skipfailures",
			'--config', 'OSM_USE_CUSTOM_INDEXING', 'NO',
			"-clipdst", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
			"-f", "ESRI Shapefile",  os.path.join(download_dir, "osm"), file_name,
			"-t_srs", "EPSG:4326", 
			"-overwrite"
			])


# TODO get layers

def make_json():
	layers = [
		"points",
		"lines",
		"multilinestrings",
		"multipolygons",
		"other_relations"
	]

	for layer in layers:
		subprocess.call([
				"ogr2ogr",
				"-skipfailures",
				'--config', 'OSM_USE_CUSTOM_INDEXING', 'NO',
				"-clipdst", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
				"-f", "GeoJSON", os.path.join(clipped_dir, "osm", layer+".json"), file_name, layer, 
				"-t_srs", "EPSG:4326", 
				# "-overwrite"
				])

if __name__ == '__main__':
	# make_shp()
	make_json()