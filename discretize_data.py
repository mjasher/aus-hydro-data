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

import numpy
import json
import csv
from osgeo import ogr, osr, gdal
import os
import copy
import datetime
# import flopy
import matplotlib.pylab as plt




"""
Converts source layer to raster (array) given a custom function ```rasterize(layer, clipping poly)``` 
	which takes the layer and polygon for once cell and returns cell's value
"""
def ogr_to_raster( source_file, nrow, ncol, bbox, rasterize, filter=False ):
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

	array = numpy.empty((nrow, ncol)).tolist()
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
			if filter:
				source_layer.SetSpatialFilter(poly)

			source_layer.ResetReading()

			array[row][col] = rasterize(source_layer, poly)

	return {
		"bottomLeft": { "lat": y_min, "lng": x_min },
		"pixelHeight": pixelHeight,
		"pixelWidth": pixelWidth,
		"array": array
	}


def rasterize_geom(geom, nrow, ncol, bbox, rasterize, filter=False):
	x_min = bbox[0][1]
	x_max = bbox[1][1]
	y_min = bbox[1][0]
	y_max = bbox[0][0]

	pixelWidth = (x_max - x_min)/ncol
	pixelHeight = (y_max - y_min)/nrow

	array = numpy.empty((nrow, ncol)).tolist()
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

			array[row][col] = rasterize(geom, poly)

	return numpy.array(array)


def contour_to_array(nrow, ncol, bbox, in_file, prop):
	# TODO use weighted average rather than simply the closest
	def rasterize_top(source_layer, clipping_poly):
		centroid = clipping_poly.Centroid()

		properties = [
			(feature.GetGeometryRef().Distance(centroid), feature.GetField(prop))
			for feature in source_layer
			if feature.GetField(prop) is not None
		]
		sorted_properties = numpy.sort(
			numpy.array(
				properties, 
				dtype = [('distance', float), (prop, float)]
			), 
			order='distance'
		)
		val = sorted_properties[0][prop]
		return val

	# contour_file = os.path.join(data_dir, "APPT250K_Contours_line.json")
	contour_file = os.path.join(data_dir, in_file)

	return ogr_to_raster( contour_file, nrow, ncol, bbox, rasterize_top)



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

# class counter():
# 	def __init__(self):
# 		self.count = 0
# 	def inc(self):
# 		self.count += 1
# 	def tot(self):
# 		return self.count


def make_del(nrow, ncol, bbox, save=False):
	x_min = bbox[0][1]
	x_max = bbox[1][1]
	y_min = bbox[1][0]
	y_max = bbox[0][0]

	# delr_deg = (x_max - x_min)/ncol
	# delc_deg = (y_max - y_min)/nrow
	# get distance in meters
	delr = projected_distance(4326, 4087, {"lng": x_min, "lat": y_min}, {"lng": x_max, "lat": y_min})/ncol 
	delc = projected_distance(4326, 4087, {"lng": x_min, "lat": y_min}, {"lng": x_min, "lat": y_max})/nrow

	return delr, delc

def make_top(nrow, ncol, bbox, save=False):
	elevation_json = contour_to_array(nrow, ncol, bbox, in_file=os.path.join(data_dir, "APPT250K_Contours_line.json"), prop='ELEVATION')
	print elevation_json
	if save:
		with open(os.path.join(dest_dir, 'elevation.json'), 'w') as f:
			f.write(json.dumps(elevation_json))

	return numpy.array(elevation_json["array"])

def make_bot(nrow, ncol, bbox, top, save=False):

	aquifer_source_file = os.path.join(data_dir, "VWAD_AQ.json")

	aquifer_terms = {
			"Calivil":	["Upper Tertiary Aquifer (fluvial)", "Calivil Fm"],
			"Renmark":	["Renmark"],
			"Shepparton":	["Shepparton F"],
			"Coliban":	["basalt"],
			"aeolian": ["Various aeolian deposits"],
			}

	aquifers = {k: ogr.Geometry(ogr.wkbPolygon) for k in aquifer_terms}

	source_ds = ogr.Open(aquifer_source_file)
	source_layer = source_ds.GetLayer()
	for feature in source_layer:
		GEOVAFGEOL = feature.GetField("GEOVAFGEOL")
		for k, ts in aquifer_terms.iteritems():
			for term in ts:
				if term in GEOVAFGEOL:
					aquifers[k] = aquifers[k].Union(feature.GetGeometryRef())
	

	if save:
		geojson = {"type": "FeatureCollection", "features": []}
		for k, a in aquifers.iteritems():
			geojson["features"].append({
					"type": "Feature",
					"geometry": json.loads(a.ExportToJson()),
					"properties": {
						"name": '/'.join(aquifer_terms[k])
					}
				})
		with open(os.path.join(data_dir,'vwad_aquifers.json'), 'w') as f:
			f.write(json.dumps(geojson))


	ibound = []
	bot = []
	hk = []
	sy = []
	ss = []
	laytyp = []
	laycbd = []

	def rasterize_ibound(geom, clipping_poly):
		if geom.Intersection(clipping_poly).Area()/clipping_poly.Area() > 0.1:
			return 1
		else:
			return 0

	Coliban = rasterize_geom(aquifers["Coliban"], nrow, ncol, bbox, rasterize_ibound, filter=False)
	Shepparton = rasterize_geom(aquifers["Shepparton"], nrow, ncol, bbox, rasterize_ibound, filter=False)
	hk = numpy.zeros((nrow, ncol))
	hk[Coliban > 0] = 0.01
	hk[Shepparton > 0] = 2.
	sy = numpy.zeros((nrow, ncol))
	sy[Coliban > 0] = 0.00001
	sy[Shepparton > 0] = 0.015

	ibound.append(Coliban+Shepparton)
	bot.append(top - 63.)
	hk.append(hk)
	sy.append(sy)
	ss.append(sy/1e3)
	laytyp.append(1)
	laycbd.append(0)


	Calivil = rasterize_geom(aquifers["Calivil"], nrow, ncol, bbox, rasterize_ibound, filter=False)
	hk = numpy.zeros((nrow, ncol))
	hk[Calivil > 0] = 50
	sy = numpy.zeros((nrow, ncol))
	sy[Calivil > 0] = 0.1

	ibound.append(Calivil)
	bot.append(top - 85.)
	hk.append(hk)
	# sy.append(sy)
	ss.append(sy/1e3)
	laytyp.append(0)
	laycbd.append(0)

	Renmark = rasterize_geom(aquifers["Renmark"], nrow, ncol, bbox, rasterize_ibound, filter=False)
	hk = numpy.zeros((nrow, ncol))
	hk[Renmark > 0] = 70
	sy = numpy.zeros((nrow, ncol))
	sy[Renmark > 0] = 0.1

	ibound.append(Renmark)
	bot.append(top - 122.)
	hk.append(hk)
	# sy.append(sy)
	ss.append(sy/1e3)
	laytyp.append(0)
	laycbd.append(0)
	
	return ibound, bot, hk, sy, ss, laytyp, laycbd





	# for i,a in enumerate(aquifers):
	# 	ibound.append( rasterize_geom(a, nrow, ncol, bbox, rasterize_ibound, filter=False) )
	# 	bot.append( rasterize_geom(a, nrow, ncol, bbox, rasterize_bot, filter=False) )




	



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
		return numpy.sum(properties)


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
		properties = numpy.array([
			[feature.GetGeometryRef().Clone().Intersection(clipping_poly).Area(),
				feature.GetField('HydKValue'), feature.GetField('SpecYield')]
			for feature in source_layer
			# if feature.GetField('HydKValue') != None
		])
		if len(properties) == 0 or numpy.sum(properties[:,0]) == 0:
			return [-9999, -9999]
		else:
			return [numpy.average(properties[:,1], weights=properties[:,0]), numpy.average(properties[:,2], weights=properties[:,0])]


	hk_sy_mean =  ogr_to_raster(
			os.path.join(data_dir, "IGWWaterTableHydraulicConductivity.json"),
			nrow, ncol,
			bbox,
			rasterize_hk_sy,
			True
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
	
	# get bore level below site
	# =============================================================================
	# 110.? and 111.? are Bore level 
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

			values = [float(r["Value"]) for r in rows]
			dates = [datetime.datetime.strptime(r["Time"], "%Y%m%d%H%M%S") for r in rows]

			day_dot = datetime.datetime(2008,1,1) # make sure this is before the first day
			# interp_dates = [datetime.datetime(2010,4,16), datetime.datetime(2013,2,22), datetime.datetime(2014,4,1), datetime.datetime(2014,12,31) ]
			interp_dates = [datetime.datetime(2015,6,1)]
			interp_values = numpy.interp([(d - day_dot).days for d in interp_dates], [(d - day_dot).days for d in dates], values)


			# print rows[0], variable_info["name"], ' - ', variable_info["subdesc"]
			# print datetime.strptime(rows[-1]["Time"], "%Y%m%d%H%M%S") # "yyyymm22hhiiee" YYYYMMDDhhmmss
			groundwater_sites.append({
				"lat": feat["geometry"]["coordinates"][1],
				"lng": feat["geometry"]["coordinates"][0],
				'values': values,
				'dates': [r["Time"] for r in rows],
				"bore level below": interp_values[0],
				"station": feat["properties"]["station"],
				})

	# 		plt.plot(dates, values, alpha=0.7, label=feat["properties"]["station"])
	# plt.legend()
	# plt.show()

	'''
	yearly small around 20, WRK953020,WRK953014, WRK953015 ]
	[ yearly big around 15-30 110152, 89586]
	 [ small around 15 WRK953018, WRK953019]
	 [ very small around 0, WRK953017, 89579
	 10-15 110151, 110153 ( 110151 much more variation sometimes with big (110152, 89586))

	WRK953014
	WRK953015
	WRK953020

	110152
	89586

	110151

	WRK953018
	WRK953019

	110153

	WRK953017
	89579

	JUNK
	WRK953016
	WRK953021

	'''

	print len(groundwater_sites), "sites"

	import fetch_data.google_elevation
	print fetch_data.google_elevation.get_elevations(groundwater_sites, dest_dir)


	# get elevation at sites
	# =============================================================================
	# with open(os.path.join(dest_dir, "elevation.json")) as f:
	# 	elevations = json.loads(f.read())

	# delc = elevations["pixelHeight"] # y, lat, nrow, delc
	# delr = elevations["pixelWidth"] # x, lng, ncol, delr
	# cnr = elevations["bottomLeft"]

	# z = numpy.array(elevations["array"])
	# nrow, ncol = z.shape
	# print nrow, ncol

	# from scipy import interpolate
	# # x, y = numpy.mgrid[cnr["lng"]+(0.5)*delr : cnr["lng"]+(ncol-0.5)*delr : ncol*1j , \
	# # 				cnr["lat"]+(0.5)*delc : cnr["lat"]+(nrow-0.5)*delc : nrow*1j]
	# # print x.shape
	# # print y.shape
	# # print z.shape
	# xx = numpy.linspace(cnr["lng"]+(0.5)*delr, cnr["lng"]+(ncol-0.5)*delr, ncol)
	# yy = numpy.linspace(cnr["lat"]+(0.5)*delc, cnr["lat"]+(nrow-0.5)*delc, nrow)
	# x, y = numpy.meshgrid(xx, yy)

	# tck = interpolate.bisplrep(x, y, z, s=0)

	# spline_znew = interpolate.bisplev([s['lng'] for s in groundwater_sites], [s['lat'] for s in groundwater_sites], tck)
	# print spline_znew
	# # spline_znew = interpolate.bisplev(xnew[:,0], ynew[0,:], tck)

	# # rbf = interpolate.Rbf(x, y, z, epsilon=2)
	# # rbf_znew = rbf(xnew, ynew)

	# TODO cut up APPT250K_Contours_line into points with elevation value, use for interpolation.



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
	data_dir = "/home/mikey/Desktop/aus-hydro-data/clipped_data/"
	dest_dir = "/home/mikey/Desktop/aus-hydro-data/raster_data/"
	bbox = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
	nrow, ncol = (40, 20)
	
	save = False
	# delr, delc = make_del(nrow, ncol, bbox, save=save)
	top = make_top(nrow, ncol, bbox, save=save)
	ibound, bot, hk, sy, ss, laytyp, laycbd = make_bot(nrow, ncol, bbox, top=top, save=save)


	# make_dis(nrow, ncol, bbox)
	# make_elev(nrow, ncol, bbox)
	# make_ibound(nrow, ncol, bbox)
	# make_riv(nrow, ncol, bbox)
	# make_hk_sy(nrow, ncol, bbox)
	# make_strt(nrow, ncol, bbox)

	# test_dis(nrow=80, ncol=40, bounding_box=bbox)
