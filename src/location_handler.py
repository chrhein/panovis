from math import radians, asin, cos, sin, atan2, degrees

import rasterio
from osgeo import ogr, osr
from rasterio.warp import transform


def get_location(lat, lon, hgt, look_at_lat, look_at_lon, look_at_hgt):
    return [[lat, lon, hgt], [look_at_lat, look_at_lon, look_at_hgt]]


def convert_coordinates(raster, to_espg, lat, lon, is_camera):
    b = raster.bounds
    min_x, min_y, max_x, max_y = b.left, b.bottom, b.right, b.top
    coordinate_pair = cor_to_crs(to_espg, lat, lon)
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
    height_max = (max_x - min_x)
    height_scaled = (height - height_min) / (height_max - height_min)
    height_max_mountain = h.max()
    height_max_mountain_scaled = (height - height_min) /\
                                 (height_max_mountain - height_min)
    if is_camera:
        height_scaled = height_scaled * 1.57  # to place camera above horizon
    return [lat_scaled, height_scaled*0.75,
            lon_scaled, height_max_mountain_scaled*0.75]


def cor_to_crs(to_espg, lat, lon):
    in_sr = osr.SpatialReference()
    in_sr.ImportFromEPSG(4326)
    out_sr = osr.SpatialReference()
    out_sr.ImportFromEPSG(to_espg)
    coordinate_pair = ogr.Geometry(ogr.wkbPoint)
    coordinate_pair.AddPoint(lat, lon)
    coordinate_pair.AssignSpatialReference(in_sr)
    coordinate_pair.TransformTo(out_sr)
    return coordinate_pair


def crs_to_cor(to_espg, lat, lon):
    in_sr = osr.SpatialReference()
    in_sr.ImportFromEPSG(4326)
    out_sr = osr.SpatialReference()
    out_sr.ImportFromEPSG(to_espg)
    coordinate_pair = ogr.Geometry(ogr.wkbPoint)
    coordinate_pair.AddPoint(lat, lon)
    coordinate_pair.AssignSpatialReference(out_sr)
    coordinate_pair.TransformTo(in_sr)
    return coordinate_pair


def crs_to_wgs84(dataset, x, y):
    crs = rasterio.crs.CRS.from_epsg(4326)
    lon, lat = transform(dataset.crs, crs, xs=[x], ys=[y])
    return lat, lon


def look_at_location(in_lat, in_lon, dist_in_kms, true_course):
    earth_radius = 6378.1
    bearing = radians(true_course)
    d = dist_in_kms
    lat1, lon1 = radians(in_lat), radians(in_lon)
    lat2 = asin(sin(lat1) * cos(d / earth_radius)
                + cos(lat1) * sin(d / earth_radius) * cos(bearing))
    lon2 = lon1 + atan2(sin(bearing) * sin(d / earth_radius)
                                     * cos(lat1), cos(d / earth_radius)
                        - sin(lat1) * sin(lat2))
    lat2, lon2 = degrees(lat2), degrees(lon2)
    return lat2, lon2
