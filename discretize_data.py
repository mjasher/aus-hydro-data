"""

line cutting (averaging)
RIV

point interpolation then gridding (averaging) 
or just interpolate to centre of cell
RCH

polygon intersection (averaging)
HK, SS

point cutting or dividing between nearby cells?
WEL


======================

What is conductance? (MODFLOW help)
---------------
Darcy's law states that
Q = -KA(h1 - h0)/(X1 - X0)
Where Q is the flow (L3/T)
K is the hydraulic conductivity (L/T)
A is the area perpendicular to flow (L2)
h is head (L)
X is the position at which head is measured (L)
Conductance combines the K, A and X terms so that Darcy's law can be expressed as
Q = -C(h1 - h0)
where C is the conductance (L2/T)



Gdal resources
---------------

https://github.com/dwtkns/gdal-cheat-sheet
https://pcjericks.github.io/py-gdalogr-cookbook/projection.html
http://gdal.org/python/


Old
---------------

/home/mikey/Dropbox/pce/agu/python/
	final_flopy_api.py
	run_final_flopy_api.py
	shp_to_ibound.py
	ogr_to_modflow.py
	bom_to_geojson.py
	grid.py
	fetch_nsw_water_data.py
etc. 

"""

import numpy as np
import json
import csv
from osgeo import ogr, osr, gdal
import os
import copy
import time
# import flopy




"""
Converts source layer to raster (array) given a custom function ```rasterize(layer, clipping poly)``` 
	which takes the layer and polygon for once cell and returns cell's value
"""
def ogr_to_raster( source_file, nrow, ncol, bbox, rasterize ):
	# open source (file)
	source_ds = ogr.Open(source_file)
	source_layer = source_ds.GetLayer()

	# to ensure cut geometries (like ibound) remain consistent
	# x_min, x_max, y_min, y_max = source_layer.GetExtent()
	# print x_min == bbox[0][1], x_max == bbox[1][1], y_min == bbox[1][0], y_max == bbox[0][0]
	x_min = bbox[0][1]
	x_max = bbox[1][1]
	y_min = bbox[1][0]
	y_max = bbox[0][0]

	pixelWidth = (x_max - x_min)/ncol
	pixelHeight = (y_max - y_min)/nrow

	array = np.empty((nrow, ncol)).tolist()
	for row in range(nrow):
		for col in range(ncol):

			# Create clipping polygon
			ring = ogr.Geometry(ogr.wkbLinearRing)
			ring.AddPoint(x_min+(col)*pixelWidth, y_min+(row)*pixelHeight)
			ring.AddPoint(x_min+(col+1)*pixelWidth, y_min+(row)*pixelHeight)
			ring.AddPoint(x_min+(col+1)*pixelWidth, y_min+(row+1)*pixelHeight)
			ring.AddPoint(x_min+(col)*pixelWidth, y_min+(row+1)*pixelHeight)
			ring.AddPoint(x_min+(col)*pixelWidth, y_min+(row)*pixelHeight)
			poly = ogr.Geometry(ogr.wkbPolygon)
			poly.AddGeometry(ring)
			
			# speeds things up but breaks them too
			# source_layer.SetSpatialFilterRect(x_min+col*pixelWidth, x_min+(col+1)*pixelWidth, y_min+row*pixelHeight, y_min+(row+1)*pixelHeight)
			# speeds them up, doesn't seem to break them
			source_layer.SetSpatialFilter(poly)

			source_layer.ResetReading()

			array[row][col] = rasterize(source_layer, poly)

	return {
		"bottomLeft": { "lat": y_min, "lng": x_min },
		"pixelHeight": pixelHeight,
		"pixelWidth": pixelWidth,
		"array": array
	}


"""
Calculates distance in EPSG:to_epsg of two points in EPSG:from_epsg

Note: 
epsg4087 has equal distance so is good for raster (http://spatialreference.org/ref/sr-org/epsg4087-wgs-84-world-equidistant-cylindrical/).


"""
def projected_distance(from_epsg, to_epsg, p1, p2):
	p1_geo = ogr.Geometry(ogr.wkbPoint)
	p1_geo.AddPoint(p1["lng"], p1["lat"])			
	p2_geo = ogr.Geometry(ogr.wkbPoint)
	p2_geo.AddPoint(p2["lng"], p2["lat"])

	inSpatialRef = osr.SpatialReference()
	inSpatialRef.ImportFromEPSG(from_epsg)

	outSpatialRef = osr.SpatialReference()
	outSpatialRef.ImportFromEPSG(to_epsg)

	# create the CoordinateTransformation
	transform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)	

	p1_geo.Transform(transform)
	p2_geo.Transform(transform)

	return p1_geo.Distance(p2_geo)

def make_dis(nrow, ncol, bbox):

	x_min = bbox[0][1]
	x_max = bbox[1][1]
	y_min = bbox[1][0]
	y_max = bbox[0][0]

	# delr_deg = (x_max - x_min)/ncol
	# delc_deg = (y_max - y_min)/nrow

	# get distance in meters
	delr = projected_distance(4326, 4087, {"lng": x_min, "lat": y_min}, {"lng": x_max, "lat": y_min})/ncol 
	delc = projected_distance(4326, 4087, {"lng": x_min, "lat": y_min}, {"lng": x_min, "lat": y_max})/nrow

	# TODO use weighted average rather than simply the closest

	def rasterize_top(source_layer, clipping_poly):
		centroid = clipping_poly.Centroid()

		properties = [
			(feature.GetGeometryRef().Distance(centroid), feature.GetField('ContValue'))
			for feature in source_layer
			if feature.GetField('ContValue') is not None
		]
		sorted_properties = np.sort(
			np.array(
				properties, 
				dtype = [('distance', float), ('ContValue', float)]
			), 
			order='distance'
		)
		val = sorted_properties[0]['ContValue']
		return val

	# contour_file = os.path.join(data_dir, "APPT250K_Contours_line.json")
	contour_file = os.path.join(data_dir, "AHGFAquiferContour.json")

	top_json = ogr_to_raster( contour_file, nrow, ncol, bbox, rasterize_top)
	top_json["extra"] = {"delr": delr, "delc": delc}
	with open(os.path.join(dest_dir, 'top.json'), 'w') as f:
		f.write(json.dumps(top_json))

	print "delr, delc", delr, delc


def make_ibound(nrow, ncol, bbox):

	catchment_file = os.path.join(data_dir, "Campaspe_GCU.json")

	def rasterize_ibound(source_layer, clipping_poly):
		feature = source_layer.GetFeature(0)
		geom = feature.GetGeometryRef()
		if geom.Intersection(clipping_poly).Area()/clipping_poly.Area() > 0.1:
			return 1
		else:
			return 0

	ibound_json = ogr_to_raster(catchment_file, nrow, ncol, bbox, rasterize_ibound)

	with open(os.path.join(dest_dir, 'ibound.json'), 'w') as f:
		f.write(json.dumps(ibound_json))


def make_riv(nrow, ncol, bbox):
	river_file = os.path.join(data_dir,"AHGFNetworkStream.json")

	# transform so we can use length of river in meters
	inDs = ogr.Open(river_file)
	inLayer = inDs.GetLayer()
	inSpatialRef = inLayer.GetSpatialRef()

	# output SpatialReference, we want meters for modflow
	outSpatialRef = osr.SpatialReference()
	outSpatialRef.ImportFromEPSG(4087)

	# create the CoordinateTransformation
	transform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

	def rasterize_riv(source_layer, clipping_poly):
		properties = []
		for feature in source_layer:
			if feature.GetField('Hierarchy') == "Major":	
				clipped = clipping_poly.Clone().Intersection(feature.GetGeometryRef())
				# clipped = feature.GetGeometryRef().Clone().Intersection(clipping_poly)
				clipped.Transform(transform)
				properties.append(clipped.Length())
		return np.sum(properties)


	raster =  ogr_to_raster(
		river_file,
		nrow, ncol,
		bbox,
		rasterize_riv) 
	
	with open(os.path.join(dest_dir, "riv.json"), 'w') as f:
			f.write(json.dumps(raster))


def make_hk_sy(nrow, ncol, bbox):
	# TODO vka and ss 

	def rasterize_hk_sy(source_layer, clipping_poly):
		properties = np.array([
			[feature.GetGeometryRef().Clone().Intersection(clipping_poly).Area(),
				feature.GetField('HydKValue'), feature.GetField('SpecYield')]
			for feature in source_layer
			# if feature.GetField('HydKValue') != None
		])
		if len(properties) == 0 or np.sum(properties[:,0]) == 0:
			return [-9999, -9999]
		else:
			return [np.average(properties[:,1], weights=properties[:,0]), np.average(properties[:,2], weights=properties[:,0])]


	hk_sy_mean =  ogr_to_raster(
			os.path.join(data_dir, "IGWWaterTableHydraulicConductivity.json"),
			nrow, ncol,
			bbox,
			rasterize_hk_sy
			) 

	hk_copy = copy.deepcopy(hk_sy_mean)
	sy_copy = copy.deepcopy(hk_sy_mean)
	for row in range(nrow):
		for col in range(ncol):
			hk_copy["array"][row][col] = hk_copy["array"][row][col][0] 
			sy_copy["array"][row][col] = sy_copy["array"][row][col][1] 
		
	with open(os.path.join(dest_dir, "hk_mean.json"), 'w') as f:
			f.write(json.dumps(hk_copy))

	with open(os.path.join(dest_dir, "sy_mean.json"), 'w') as f:
			f.write(json.dumps(sy_copy))


def make_strt(nrow, ncol, bbox):
	# 110.00
	# 111
	with open(os.path.join(data_dir, "kisters_sites_with_data.json")) as f:
		kisters_sites = json.loads(f.read())

	groundwater_sites = []
	for feat in kisters_sites["features"]:
		
		# groundwater_vars = filter(lambda v: 109. < float(v["code"]) and float(v["code"]) < 112.,  feat["properties"]["variables"])
		groundwater_vars = filter(lambda v: v["code"] == "111.00",  feat["properties"]["variables"])
		
		if len(groundwater_vars) > 0:
		
			variable = groundwater_vars[0]
			variable_info = kisters_sites["properties"]["variables"][variable["code"]]
		
			with open(os.path.join('clipped_data', variable["file"])) as f:
				rows = [r for r in csv.DictReader(f)]
				print rows[0], variable_info["name"], ' - ', variable_info["subdesc"]
				print time.strptime(rows[-1]["Time"], "%Y%m%d%H%M%S") # "yyyymm22hhiiee" YYYYMMDDhhmmss
		
			groundwater_sites.append(feat)

	print len(groundwater_sites)



def make_rch(nrow, ncol, bbox):

	# bom climate
	# perhaps AHGFCatchment and links
	# perhaps kisters

	return 0

def make_wells(nrow, ncol, bbox):

	# kisters gw
	# perhpas NGIS

	return 0

def make_drain(nrow, ncol, bbox):
	return 0

def make_faults(nrow, ncol, bbox):

	# ShearDisplacementLines1M

	return 0




def test_dis(nrow, ncol, bounding_box):

	x_min = bounding_box[0][1]
	x_max = bounding_box[1][1]
	y_min = bounding_box[1][0]
	y_max = bounding_box[0][0]

	delr = (x_max - x_min)/ncol
	delc = (y_max - y_min)/nrow
	
	print "lat, lng 4326"
	print "nrow, ncol", nrow, ncol
	print "delr, delc", delr, delc

	print "meters 4087 (still uses WGS 84, epsg 3857 uses spherical mercator)"
	print "delr, delc", projected_distance(4326, 4087, {"lng": x_min, "lat": y_min}, {"lng": x_max, "lat": y_min})/ncol, 
	print projected_distance(4326, 4087, {"lng": x_min, "lat": y_min}, {"lng": x_min, "lat": y_max})/nrow
	delrs = [ projected_distance(4326, 4087, {"lng": x_min+delr*col, "lat": y_min}, {"lng": x_min+delr*(col+1.), "lat": y_min}) for col in range(ncol) ]
	delcs = [ projected_distance(4326, 4087, {"lng": x_min, "lat": y_max+delc*row}, {"lng": x_min, "lat": y_max+delc*(row+1.)}) for row in range(nrow) ]
	print "delrs", delrs
	print "delcs", delcs







if __name__ == '__main__':
	data_dir = "/home/mikey/Downloads/aus-hydro-data/clipped_data/"
	dest_dir = "/home/mikey/Downloads/aus-hydro-data/raster_data/"
	bbox = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
	nrow, ncol = (40, 20)
	
	# make_dis(nrow, ncol, bbox)
	# make_ibound(nrow, ncol, bbox)
	# make_riv(nrow, ncol, bbox)
	# make_hk_sy(nrow, ncol, bbox)
	make_strt(nrow, ncol, bbox)

	# test_dis(nrow=80, ncol=40, bounding_box=bbox)
