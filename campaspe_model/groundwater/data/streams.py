from osgeo import ogr
import os
import subprocess

import cache
import utils

"""
========================================================
Convert BOM geofabric to geojson
Download from the [BOM FTP server](ftp://ftp.bom.gov.au/anon/home/geofabric/).
It can be explored using [BOM WMS connection](http://geofabric.bom.gov.au/documentation/) or the [National Map](http://nationalmap.nicta.com.au/).

michael.james.asher@gmail.com
October 2015
========================================================
"""


@cache.money(key_func=cache.join_key)
def gdb_to_geojson(file_name, bbox, layers):
    min_x, max_x, min_y, max_y = bbox['bbox']

    dests = []
    for layer in layers:
        dest_json = file_name.replace(".gdb", "_" + layer + "_.json")
        if os.path.exists(dest_json):
            os.remove(dest_json)

        subprocess.call([
            "ogr2ogr",
            "-skipfailures",
            "-clipdst", str(min_x), str(min_y), str(max_x), str(max_y),  # xmin ymin xmax ymax
            "-f", "GeoJSON", dest_json, file_name, layer,
            "-t_srs", bbox['ref']
            ])

        dests.append(dest_json)
    return dests


"""
Th river model, given 
* levels for each reach
* inflows
* outflow
the will run and produce
* new levels for each reach
* predicted outflow

GW model will take new levels and give net inflows and outflows
"""

@cache.money(key_func=cache.join_key)
def make_riv(river_file, boundary_file, bbox, nrow, ncol, delr, delc):

    driver = ogr.GetDriverByName('ESRI Shapefile')
    boundary_dataSource = driver.Open(boundary_file, 0) # 0 means read-only. 1 means writeable.
    boundary_layer = boundary_dataSource.GetLayer()
    assert boundary_layer.GetFeatureCount() == 1
    boundary_feature = boundary_layer.GetFeature(0)
    boundary_geom = boundary_feature.GetGeometryRef()

    min_x, max_x, min_y, max_y = bbox["bbox"]
    pixelWidth = (max_x - min_x) / ncol
    pixelHeight = (max_y - min_y) / nrow
    assert pixelHeight == delc
    assert pixelWidth == delr

    layers = [
        # "AHGFNetworkConnectivityUp",
        # "AHGFNetworkConnectivityDown",
        # "AHGFNetworkStream_FS",
        "AHGFNetworkStream", # note not revealed by ogrinfo
        # "AHGFCatchment",
    ]

    jsons = gdb_to_geojson(river_file, bbox, layers)

    river_json = jsons[layers.index("AHGFNetworkStream")]

    """
    ['HydroID', 
    'AHGFFType', 'Name', 'Hierarchy', 'Perennial', 'AusHydroID', 'AusHydroEr', 'SegmentNo', 'DrainID',
    'From_Node', 'To_Node', 
    'NextDownID', 
    'Enabled', 'FlowDir', 'SrcFCName', 
    'SrcFType', 'SrcType', 'SourceID', 'FeatRel', 'FSource', 'AttrRel', 'AttrSource', 
    'PlanAcc', 'Symbol', 'TextNote', 'GeodesLen', 'UpstrGeoLn', 'UpstrDArea', 'Shape_Length']

    """
    reaches = []
    def rasterize_riv(source_layer, clipping_poly, row, col):
        properties = []
        for feature in source_layer:
            geom = feature.GetGeometryRef()
            if feature.GetField('Hierarchy') == "Major" and clipping_poly.Intersects(boundary_geom) and clipping_poly.Intersects(geom):
                
                clipped = clipping_poly.Clone().Intersection(geom)
                length = clipped.Length()

                reaches.append({
                    "length": length,
                    "row": row,
                    "col": col,
                    'HydroID': feature.GetField('HydroID'),
                    'NextDownID': feature.GetField('NextDownID'),
                    'Name': feature.GetField('Name'),
                    })

                properties.append(length)

        return sum(properties)


    raster =  utils.ogr_to_raster(
        river_json,
        nrow, ncol,
        bbox['bbox'],
        rasterize_riv) 


    reach_ids = [r['HydroID'] for r in reaches]
    next_ids = [r['NextDownID'] for r in reaches]
    tips = []
    heads = []

    for reach in reaches:
        reach['index_of_next'] = [i for i, r in enumerate(reaches) if r['HydroID'] == reach['NextDownID']]
        reach['index_of_previous'] = [i for i, r in enumerate(reaches) if r['NextDownID'] == reach['HydroID']]
        if len(reach['index_of_next']) == 0:
            tips.append(reach)
        if len(reach['index_of_previous']) == 0:
            heads.append(reach)


    return {
        "raster": raster,
        "reaches": reaches,
        "heads": heads,
        "tips": tips,
    }


if __name__ == '__main__':
    import boundary
    
    os.environ['CACHE_DIR'] = "/Volumes/PATRIOT/cache"

    downloaded_data = "/Volumes/PATRIOT/downloaded_data"
    # Geocentric_Datum_of_Australia_1994
    boundary_file = os.path.join(downloaded_data, "Campaspe_GC/Campaspe_GCU.shp")
    river_file = os.path.join(downloaded_data, "SH_Network_GDB/SH_Network.gdb")

    bbox = boundary.get_bounding_box(boundary_file)

    layers = [
        # "AHGFNetworkConnectivityUp",
        # "AHGFNetworkConnectivityDown",
        # "AHGFNetworkStream_FS",
        "AHGFNetworkStream", # note not revealed by ogrinfo
        # "AHGFCatchment",
    ]
    jsons = gdb_to_geojson(river_file, bbox, layers)
    
    print jsons[0]


