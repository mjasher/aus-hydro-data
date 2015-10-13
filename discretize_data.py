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



"""

import numpy as np
import json
import flopy
from osgeo import ogr, osr, gdal


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

	array = np.empty((nrow, ncol))
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

			source_layer.ResetReading()

			array[row, col] = rasterize(source_layer, poly)

	return {
		"bottomLeft": { "lat": y_min, "lng": x_min },
		"pixelHeight": pixelHeight,
		"pixelWidth": pixelWidth,
		"array": array.tolist()
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

	# contour_file = "/home/mikey/Downloads/aus-hydro-data/clipped_data/APPT250K_Contours_line.json"
	contour_file = "/home/mikey/Downloads/aus-hydro-data/clipped_data/AHGFAquiferContour.json"

	top_json = ogr_to_raster( contour_file, nrow, ncol, bbox, rasterize_top)
	top_json["extra"] = {"delr": delr, "delc": delc}
	with open('/home/mikey/Downloads/aus-hydro-data/raster_data/top.json', 'w') as f:
		f.write(json.dumps(top_json))

	print "delr, delc", delr, delc



def make_ibound(nrow, ncol, bbox):

	catchment_file = "/home/mikey/Downloads/aus-hydro-data/clipped_data/Campaspe_GCU.json"

	def rasterize_ibound(source_layer, clipping_poly):
		feature = source_layer.GetFeature(0)
		geom = feature.GetGeometryRef()
		if geom.Intersection(clipping_poly).Area()/clipping_poly.Area() > 0.1:
			return 1
		else:
			return 0

	ibound_json = ogr_to_raster(catchment_file, nrow, ncol, bbox, rasterize_ibound)

	with open('/home/mikey/Downloads/aus-hydro-data/raster_data/ibound.json', 'w') as f:
		f.write(json.dumps(ibound_json))


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




def make_hk():
	return 0

def make_ss():
	return 0


if __name__ == '__main__':
	bbox = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
	nrow, ncol = (40, 20)
	# make_dis(nrow, ncol, bbox)
	make_ibound(nrow, ncol, bbox)


	# test_dis(nrow=80, ncol=40, bounding_box=bbox)
