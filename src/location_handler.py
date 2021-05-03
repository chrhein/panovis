import rasterio
from osgeo import ogr, osr
from rasterio.warp import transform


def get_location(lat, lon, hgt, look_at_lat, look_at_lon, look_at_hgt):
    location_x = lat
    location_y = lon
    location_height = hgt
    view_x = look_at_lat
    view_y = look_at_lon
    view_height = look_at_hgt
    return [[location_x, location_y, location_height], [view_x, view_y, view_height]]


def convert_coordinates(raster, to_espg, lat, lon):
    b = raster.bounds
    min_x, min_y, max_x, max_y = b.left, b.bottom, b.right, b.top

    in_sr = osr.SpatialReference()
    in_sr.ImportFromEPSG(4326)  # WGS84/Geographic
    out_sr = osr.SpatialReference()
    out_sr.ImportFromEPSG(to_espg)

    coordinate_pair = ogr.Geometry(ogr.wkbPoint)
    coordinate_pair.AddPoint(lat, lon)
    coordinate_pair.AssignSpatialReference(in_sr)
    coordinate_pair.TransformTo(out_sr)

    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()
    lat_scaled = (polar_lat - min_x) / (max_x - min_x)
    lon_scaled = (polar_lon - min_y) / (max_y - min_y)

    to_crs = raster.crs
    from_crs = rasterio.crs.CRS.from_epsg(4326)
    new_x, new_y = transform(from_crs, to_crs, [lon], [lat])
    new_x = new_x[0]
    new_y = new_y[0]
    row, col = raster.index(new_x, new_y)
    h = raster.read(1)
    height = h[row][col]
    height_min = h.min()
    height_max = h.max()
    height_scaled = (height - height_min) / (height_max - height_min)
    return [lat_scaled, lon_scaled, height_scaled / 38]
