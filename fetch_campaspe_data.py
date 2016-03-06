
"""
This is a selection of scripts to download data from Australian government websites for hydrological modelling.
The example is the Campaspe catchment in Victoria.

michael.james.asher@gmail.com
October 2015

Data and functions to gather it
--------------------------------------------
Victorian aquifer framework (ftp://ftp1.land.vic.gov.au/VAF/)
``` fetch_data.vaf ```

Clipping shape [Campaspe GW Catchment](https://www.data.vic.gov.au/data/dataset/groundwater-catchments-gc)
``` clippping_shape() ```

BOM Geofabric downloaded from the [BOM FTP server](ftp://ftp.bom.gov.au/anon/home/geofabric/).
It can be explored using [BOM WMS connection](http://geofabric.bom.gov.au/documentation/) or the [National Map](http://nationalmap.nicta.com.au/).
``` fetch_data.geofabric ```

Mapconnect geology data. Downloaded elevation contours and watercourses extract from [Mapconnect](http://mapconnect.ga.gov.au/MapConnect/250K/)
``` fetch_data.mapconnect ```

BOM climate time series (http://www.bom.gov.au/climate/data)
``` fetch_data.bom ```

State water data (http://data.water.vic.gov.au/monitoring.htm)
``` fetch_data.kisters_hydrology ```

Geology data from  GA [Surface Geology of Australia 1:1 million scale dataset 2012 edition](http://www.ga.gov.au/metadata-gateway/metadata/record/gcat_c8856c41-0d5b-2b1d-e044-00144fdd4fa6/Surface+Geology+of+Australia+1%3A1+million+scale+dataset+2012+edition) by downloading the [shapefile](http://www.ga.gov.au/corporate_data/74619/74619_1M_shapefiles.zip).
Faults: ShearDisplacementLines1M, GeologicUnitPolygons1M.
``` fetch_data.ga_geology ```

Aquifers from the [Victorian Water Asset Database (VWAD) - AQUIFER_LAYER](https://www.data.vic.gov.au/data/dataset/victorian-water-asset-database-vwad-aquifer_layer)
``` fetch_data.vwad ```


Other potential sources of data
--------------------------------------------

[Visualizing Victoria's Groundwater](http://www.vvg.org.au/cb_pages/export.php)

From the [BOM groundwater explorer](http://www.bom.gov.au/water/groundwater/explorer/) download ngis_shp_VIC.zip.

Climate data from [Long Paddock](http://www.longpaddock.qld.gov.au/silo)

Department of Agriculture and Water Resources [ACLUMP land use data](http://www.agriculture.gov.au/abares/aclump/land-use/data-download)

[Soil and Landscape Grid of Australia](http://www.clw.csiro.au/aclep/soilandlandscapegrid/)

[GW and SW data](http://data.water.vic.gov.au/monitoring.htm)

[Vic. deep leads](http://www.data.vic.gov.au/data/dataset/geological-deep-leads-1-250-000)

[Groundwater Resource Report] (http://www.depi.vic.gov.au/water/groundwater/groundwater-resource-reports)
[Campaspe report](http://gwv.cloudapp.net/aquiferservice/Report/aquiferreport201510080859405324950.html)

"""

import subprocess
import os

bounding_box = [[-35.752101, 144.192687], [-37.450203, 145.022532]] #  top left, bottom right
destination_dir = "clipped_data"

def clipping_shape():
	file_name = "downloaded_data/Campaspe_GC/Campaspe_GCU.shp"
	subprocess.call([
		"ogr2ogr",
		# "-clipsrc", str(bounding_box[0][1]), str(bounding_box[0][0]), str(bounding_box[1][1]), str(bounding_box[1][0]),
		"-f", "GeoJSON", os.path.join(destination_dir,os.path.basename(file_name).replace(".shp",".json")), file_name,
		"-t_srs", "EPSG:4326" 
		])

if __name__ == '__main__':
	
	# clipping_shape()
	
	from fetch_data import kisters_hydrology, geofabric, mapconnect, bom, ga_geology, vwad

	# water data from Vic. state government
	# kisters_hydrology.run(bounding_box, destination_dir)
	
	# geology from BOM geofabric
	# geofabric.run(bounding_box, destination_dir)

	# geology from GA mapconnect
	# mapconnect.run(bounding_box, destination_dir)
	
	# climate data from BOM
	# bom.run(bounding_box, destination_dir)

	# faults from GA
	# ga_geology.run(bounding_box, destination_dir)

	# aquifers from data.vic.gov.au
	vwad.run(bounding_box, destination_dir)

	# google_elevation
	# bulk bores vic_water_bores


"""
Required:

* bores with extraction data
* rainfall, temperature for recharge
* land use for recharge
* river location and level
* conductivity and storativity
* bores with hydrographs for calibration

"""