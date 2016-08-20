"""
Clipping shape [Campaspe GW Catchment](https://www.data.vic.gov.au/data/dataset/groundwater-catchments-gc)
"""

from osgeo import ogr
from osgeo import osr
import numpy as np
import cache
import utils

@cache.money(key_func=lambda x: 'one')
def get_bounding_box(boundary_file):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    boundary_dataSource = driver.Open(boundary_file, 0) # 0 means read-only. 1 means writeable.
    boundary_layer = boundary_dataSource.GetLayer()
    assert boundary_layer.GetFeatureCount() == 1
    boundary_feature = boundary_layer.GetFeature(0)
    boundary_geom = boundary_feature.GetGeometryRef()

    # from_ref = boundary_geom.GetSpatialReference()
    # wgs84_ref = osr.SpatialReference()
    # wgs84_ref.SetWellKnownGeogCS( "WGS84" );  # equivalently unprojected.ImportFromEPSG(4326) or unprojected.SetWellKnownGeogCS( "EPSG:4326" );
    # to_wgs84 = osr.CoordinateTransformation(from_ref, wgs84_ref)
    # boundary_geom.Transform(to_wgs84)
    # min_lng, max_lng, min_lat, max_lat = boundary_geom.GetEnvelope()

    min_x, max_x, min_y, max_y = boundary_geom.GetEnvelope()

    # round to nearest km
    min_x = 1000. * np.floor(min_x / 1000)
    max_x = 1000. * np.ceil(max_x / 1000)
    min_y = 1000. * np.floor(min_y / 1000)
    max_y = 1000. * np.ceil(max_y / 1000)

    ref = boundary_geom.GetSpatialReference().ExportToWkt()

    return {
        "bbox": (min_x, max_x, min_y, max_y),
        "min_x": min_x,
        "max_x": max_x,
        "min_y": min_y,
        "max_y": max_y,
        "ref": ref,
    }


@cache.money(key_func=cache.join_key)
def get_ibound(boundary_file, bbox, nrow, ncol, delr, delc):
    min_x, max_x, min_y, max_y = bbox['bbox']

    driver = ogr.GetDriverByName('ESRI Shapefile')
    boundary_dataSource = driver.Open(boundary_file, 0) # 0 means read-only. 1 means writeable.
    boundary_layer = boundary_dataSource.GetLayer()
    assert boundary_layer.GetFeatureCount() == 1
    boundary_feature = boundary_layer.GetFeature(0)
    boundary_geom = boundary_feature.GetGeometryRef()

    assert bbox['ref'] == boundary_geom.GetSpatialReference().ExportToWkt()

    nlay = 1 # TODO
    ibound = np.ones((nlay, nrow, ncol), dtype=np.int32)
    for i in range(ibound.shape[1]):
        for j in range(ibound.shape[2]):
          # pixel to coord
          x = min_x + (j + 0.5) * delr
          y = min_y + (i + 0.5) * delc

          wkt = "POINT (%f %f)" % (x, y)
          point = ogr.CreateGeometryFromWkt(wkt)

          if not point.Within(boundary_geom):
            ibound[:, i, j] = 0

    return ibound
