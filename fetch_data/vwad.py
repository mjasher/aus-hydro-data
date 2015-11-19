"""
========================================================
Aquifers from the [Victorian Water Asset Database (VWAD)-AQUIFER_LAYER](https://www.data.vic.gov.au/data/dataset/victorian-water-asset-database-vwad-aquifer_layer)

michael.james.asher@gmail.com
October 2015
========================================================

"""



import subprocess
import os

def run(bounding_box, destination_dir):
	file_name = "downloaded_data/VWAD/VWAD_AQ.shp"
	subprocess.call([
		"ogr2ogr",
		"-clipsrc", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
		"-f", "GeoJSON", os.path.join(destination_dir,os.path.basename(file_name).replace(".shp",".json")), file_name,
		"-t_srs", "EPSG:4326" 
		])

	file_name = "downloaded_data/deep_leads/deepld250_polygon.shp"
	subprocess.call([
		"ogr2ogr",
		"-clipsrc", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
		"-f", "GeoJSON", os.path.join(destination_dir,os.path.basename(file_name).replace(".shp",".json")), file_name,
		"-t_srs", "EPSG:4326" 
		])


def union():
	from osgeo import ogr, osr, gdal
	import json

	aquifer_terms = [["Upper Tertiary Aquifer (fluvial)", "Calivil Fm"],
			["Renmark"],
			["Shepparton F"],
			["basalt"],
			["Various aeolian deposits"],]

	aquifers = [ ogr.Geometry(ogr.wkbPolygon) for i in aquifer_terms ]
	source_file = "../clipped_data/VWAD_AQ.json"

	source_ds = ogr.Open(source_file)
	source_layer = source_ds.GetLayer()
	for feature in source_layer:
		GEOVAFGEOL = feature.GetField("GEOVAFGEOL")
		for i, ts in enumerate(aquifer_terms):
			for term in ts:
				if term in GEOVAFGEOL:
					aquifers[i] = aquifers[i].Union(feature.GetGeometryRef())

	
	geojson = {"type": "FeatureCollection", "features": []}
	for i,a in enumerate(aquifers):
		geojson["features"].append({
				"type": "Feature",
				"geometry": json.loads(a.ExportToJson()),
				"properties": {
					"name": '/'.join(aquifer_terms[i])
				}
			})
	with open('../clipped_data/vwad_aquifers.json', 'w') as f:
		f.write(json.dumps(geojson))

	
def explore():
	import json
	with open('../clipped_data/VWAD_AQ.json') as f:
		aquifers = json.loads(f.read())

	for a in aquifers["features"]:
		if True or (not "Calivil" in a["properties"]["GEOVAFGEOL"]) and \
			(not "Renmark" in a["properties"]["GEOVAFGEOL"]) and \
			(not "Shepparton" in a["properties"]["GEOVAFGEOL"]) and \
			(not "basalt" in a["properties"]["GEOVAFGEOL"]):
			print a["properties"]["SHAPE_AREA"],
			print a["properties"]["GEOVAFGEOL"],
			print a["properties"]["ASSETID"]
	
	import matplotlib.pylab as plt

	# plt.hist([a["properties"]["SHAPE_AREA"] for a in aquifers["features"]], bins=100)
	# plt.show()
	print 'irrigation', [a["properties"]["ASSETNAME"] for a in aquifers["features"] if a["properties"]["ECO_IRRGTN"] is not None]	

	print "all,"
	print sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"]])
	print "==============="



	print "Calivil Fm: ", 
	Calivil = sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Upper Tertiary Aquifer (fluvial)" in a["properties"]["GEOVAFGEOL"] or "Calivil Fm" in a["properties"]["GEOVAFGEOL"]])
	print Calivil 
	print "Renmark: ", 
	Renmark = sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Renmark" in a["properties"]["GEOVAFGEOL"]])
	print Renmark
	print "Shepparton Fm: ", 
	Shepparton = sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Shepparton Fm" in a["properties"]["GEOVAFGEOL"]])
	print Shepparton
	print "basalt: ", 
	basalt = sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "basalt" in a["properties"]["GEOVAFGEOL"]])
	print basalt
	print "Various aeolian deposits: ", 
	Various = sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Various aeolian deposits" in a["properties"]["GEOVAFGEOL"]])
	print Various

	print "==============="
	print Calivil + Renmark + Shepparton + basalt + Various


	'''
	print aquifers["features"][0]["properties"].keys()
	[u'SHAPE_AREA', u'NOTES', u'MAP_AVLBLE', u'ECO_IRRGTN', u'PCF_ASSET', u'ENV_GDE', 
	u'REFERENCES', u'SFID', u'NRST_TOWN', u'ECO_WE', u'GEOVAFGEOL', u'LEG_PART_P', u'SOC_UW', 
	u'CONDITION2', u'NRM_REGION', u'MAPSHT100K', u'OTH_AT', u'LEG_PROTEC', u'WBODY_TYPE', 
	u'GISDATA_AV', u'CUR_LADUSE', u'CDLATLONG', u'SHAPE_LENG', u'CRD_DEFINE', u'ID', u'DESC', 
	u'MNG_AUTHOR', u'KNO_GAPS', u'ASSETID', u'ECO_EXPLOR', u'TENURE', u'METADAT_AV', u'ECO_TWE', 
	u'DRT_ANZMET', u'LEG_FULL_P', u'ASSETNAME', u'NWQMS_VALU', u'OTHER_GC', u'FID_ANZMET']
	'''

if __name__ == '__main__':
	explore()
	# union()