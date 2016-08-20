from osgeo import ogr
import numpy
"""
Converts source layer to raster (array) given a custom function ```rasterize(layer, clipping poly)``` 
    which takes the layer and polygon for once cell and returns cell's value
"""
def ogr_to_raster(source_file, nrow, ncol, bbox, rasterize, filter=False):
    # open source (file)
    source_ds = ogr.Open(source_file)
    source_layer = source_ds.GetLayer()

    # to ensure cut geometries (like ibound) remain consistent
    min_x, max_x, min_y, max_y = bbox

    pixelWidth = (max_x - min_x) / ncol
    pixelHeight = (max_y - min_y) / nrow

    array = numpy.empty((nrow, ncol)).tolist()
    for row in range(nrow):
        for col in range(ncol):

            # Create clipping polygon
            ring = ogr.Geometry(ogr.wkbLinearRing)
            ring.AddPoint(min_x + (col) * pixelWidth, min_y + (row) * pixelHeight)
            ring.AddPoint(min_x + (col + 1) * pixelWidth, min_y + (row) * pixelHeight)
            ring.AddPoint(min_x + (col + 1) * pixelWidth, min_y + (row + 1) * pixelHeight)
            ring.AddPoint(min_x + (col) * pixelWidth, min_y + (row + 1) * pixelHeight)
            ring.AddPoint(min_x + (col) * pixelWidth, min_y + (row) * pixelHeight)
            poly = ogr.Geometry(ogr.wkbPolygon)
            poly.AddGeometry(ring)
            
            # speeds things up but breaks them too:  source_layer.SetSpatialFilterRect(x_min+col*pixelWidth, x_min+(col+1)*pixelWidth, y_min+row*pixelHeight, y_min+(row+1)*pixelHeight)
            # speeds them up, doesn't seem to break them
            if filter:
                source_layer.SetSpatialFilter(poly)

            source_layer.ResetReading()

            array[row][col] = rasterize(source_layer, poly, row, col)

    return array


# def load_shapefile(boundary_file):
   
#     return boundary_geom
    # boundary_ref = boundary_geom.GetSpatialReference()
