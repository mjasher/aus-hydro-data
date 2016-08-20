import os
import subprocess
from osgeo import ogr
from osgeo import osr

import cache
import utils

@cache.money(key_func=cache.one_key)
def clip_wells(bore_file, bbox):
    bore_json = bore_file.replace(".shp",".json")

    if os.path.exists(bore_json):
        os.remove(bore_json)

    min_x, max_x, min_y, max_y = bbox['bbox']
    
    subprocess.call([
        "ogr2ogr",
        "-clipdst", str(min_x), str(min_y), str(max_x), str(max_y),  # xmin ymin xmax ymax
        "-f", "GeoJSON", bore_json, bore_file,
        "-t_srs", bbox['ref']   # .ExportToWkt()
        ])

    return bore_json


@cache.money(key_func=cache.join_key)
def wells_in_boundary(bore_file, boundary_file, bbox, nrow, ncol, delr, delc):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    boundary_dataSource = driver.Open(boundary_file, 0) # 0 means read-only. 1 means writeable.
    boundary_layer = boundary_dataSource.GetLayer()
    assert boundary_layer.GetFeatureCount() == 1
    boundary_feature = boundary_layer.GetFeature(0)
    boundary_geom = boundary_feature.GetGeometryRef()
    
    # boundary_ref = osr.SpatialReference()
    # boundary_ref.ImportFromWkt(bbox["ref"])

    min_x, max_x, min_y, max_y = bbox["bbox"]
    pixelWidth = (max_x - min_x) / ncol
    pixelHeight = (max_y - min_y) / nrow
    assert pixelHeight == delc
    assert pixelWidth == delr

    bore_json = clip_wells(bore_file, bbox)


    def rasterize_bores(source_layer, clipping_poly, row, col):
        return len([feature for feature in source_layer 
                    if feature.GetGeometryRef().Clone().Intersects(clipping_poly)
                    and feature.GetGeometryRef().Within(boundary_geom)])


    bore_array = utils.ogr_to_raster(bore_json, nrow, ncol, bbox['bbox'], rasterize_bores, filter=False)

    return bore_array
