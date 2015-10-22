import os
import subprocess

"""
========================================================
Convert BOM geofabric to geojson
Download from the [BOM FTP server](ftp://ftp.bom.gov.au/anon/home/geofabric/).
It can be explored using [BOM WMS connection](http://geofabric.bom.gov.au/documentation/) or the [National Map](http://nationalmap.nicta.com.au/).

michael.james.asher@gmail.com
October 2015
========================================================
"""

def gdb_to_geojson(file_name, destination_dir, layers, bounding_box):
	for layer in layers:
		subprocess.call([
			"ogr2ogr",
			"-skipfailures",
			"-clipdst", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
			"-f", "GeoJSON", os.path.join(destination_dir, layer+".json"), file_name, layer,
			# "-f", "ESRI Shapefile", destination_dir + "/" + layer+".shp", file_name, layer,
			"-t_srs", "EPSG:4326" 
			])


def run(bounding_box, destination_dir):

	file_name = "downloaded_data/GW_Cartography_GDB/GW_Cartography.gdb"
	layers = [
				"AHGFAquiferContour",
				"IGWWaterTableHydraulicConductivity",
				"AHGFWaterTableAquifer",
				"IGWWaterTableSalinity",
				"IGWAquiferSalinity",
				"IGWAquiferYield",
				"AHGFSurficialHydrogeologicUnit",
				"AHGFAquiferBoundary",
				"AHGFAquiferOutcrop",
				"IGWWaterTableYield",
			]

	gdb_to_geojson(file_name, destination_dir, layers, bounding_box)

	file_name = "downloaded_data/SH_Cartography_GDB/SH_Cartography.gdb"
	layers = [
		"AHGFMappedConnectivityDown",
		"AHGFMappedConnectivityUp",
		"AHGFMappedStream_FS",
		"AHGFHydroArea",
		"AHGFHydroPoint",
		"AHGFStructure",
		"AHGFSea",
		"AHGFTerrainBreakLine",
		"AHGFCanalLine",
		"AHGFDam",
		"AHGFHydroLine",
		"AHGFWaterPipeline",
		"AHGFEstuary",
		"SH_Cartography_Net_Junctions",
	]

	gdb_to_geojson(file_name, destination_dir, layers, bounding_box)

	file_name = "downloaded_data/SH_Network_GDB/SH_Network.gdb"
	layers = [
		"AHGFNetworkConnectivityUp",
		"AHGFNetworkConnectivityDown",
		"AHGFNetworkStream_FS",
		"AHGFNetworkStream", # note not revealed by ogrinfo
		"AHGFCatchment",
	]
	gdb_to_geojson(file_name, destination_dir, layers, bounding_box)

	file_name = "downloaded_data/SH_Catchments_GDB/SH_Catchments.gdb"
	layers =[
		"NCBPfafstetter", 
		"NCBLevel2DrainageBasinGroup", 
		"NCBLevel1DrainageDivision", 
		"AHGFCatchment", 
	]
	gdb_to_geojson(file_name, destination_dir, layers, bounding_box)

	file_name = "downloaded_data/HR_Catchments_GDB/HR_Catchments.gdb"
	layers =[
		"AHGFNodeLinkConnectivityUp",
		"AHGFNodeLinkConnectivityDown",
		"AHGFContractedCatchment",
		"AHGFNode",
		"AHGFLink",
	]
	gdb_to_geojson(file_name, destination_dir, layers, bounding_box)

	file_name = "downloaded_data/HR_Regions_GDB/HR_Regions.gdb"
	layers =[
		"RRContractedCatchmentLookup",
		"AWRADDContractedCatchmentLookup",
		"AWRADrainageDivision",
		"RiverRegion",
	]
	gdb_to_geojson(file_name, destination_dir, layers, bounding_box)


'''
Notes:

To get layer names:
ogrinfo "downloaded_data/GW_Cartography_GDB/GW_Cartography.gdb"

To get information including extent/bounding box:
ogrinfo -al -so clipped_data/Campaspe_GCU.json 
ogrinfo -al -so clipped_data/Campaspe_GCU.json  | grep Extent

left bottom - right top
>>> (144.192687, -37.450203) - (145.022532, -35.752101)

<x_min> <y_min> <x_max> <y_max>
144.192687, -37.450203, 145.022532, -35.752101]
'''