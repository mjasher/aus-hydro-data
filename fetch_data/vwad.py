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



if __name__ == '__main__':
	
	import json
	with open('../clipped_data/VWAD_AQ.json') as f:
		aquifers = json.loads(f.read())

	for a in aquifers["features"]:
		print a["properties"]["GEOVAFGEOL"],
		print a["properties"]["SHAPE_AREA"],
		print a["properties"]["ASSETID"]
	
	import matplotlib.pylab as plt

	# plt.hist([a["properties"]["SHAPE_AREA"] for a in aquifers["features"]], bins=100)
	# plt.show()
	print 'irrigation', [a["properties"]["ASSETNAME"] for a in aquifers["features"] if a["properties"]["ECO_IRRGTN"] is not None]	

	print "all"
	print "==============="
	print sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"]])

	print "Calivil Fm" 
	print "==============="
	print sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Calivil Fm" in a["properties"]["GEOVAFGEOL"]])
	print sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Renmark" in a["properties"]["GEOVAFGEOL"]])

	print "Shepparton Fm" 
	print "==============="
	print sum([a["properties"]["SHAPE_AREA"] for a in aquifers["features"] if "Shepparton Fm" in a["properties"]["GEOVAFGEOL"]])


	'''
	print aquifers["features"][0]["properties"].keys()
	[u'SHAPE_AREA', u'NOTES', u'MAP_AVLBLE', u'ECO_IRRGTN', u'PCF_ASSET', u'ENV_GDE', 
	u'REFERENCES', u'SFID', u'NRST_TOWN', u'ECO_WE', u'GEOVAFGEOL', u'LEG_PART_P', u'SOC_UW', 
	u'CONDITION2', u'NRM_REGION', u'MAPSHT100K', u'OTH_AT', u'LEG_PROTEC', u'WBODY_TYPE', 
	u'GISDATA_AV', u'CUR_LADUSE', u'CDLATLONG', u'SHAPE_LENG', u'CRD_DEFINE', u'ID', u'DESC', 
	u'MNG_AUTHOR', u'KNO_GAPS', u'ASSETID', u'ECO_EXPLOR', u'TENURE', u'METADAT_AV', u'ECO_TWE', 
	u'DRT_ANZMET', u'LEG_FULL_P', u'ASSETNAME', u'NWQMS_VALU', u'OTHER_GC', u'FID_ANZMET']
	'''
