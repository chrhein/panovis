from math import radians, asin, cos, sin, atan2, degrees
import rasterio
from osgeo import ogr, osr
from rasterio.warp import transform
from tools.types import Location
from functools import reduce
import operator
from numpy import sin, cos, degrees

# constants
EARTH_RADIUS = 6378.1


def get_earth_radius():
    return EARTH_RADIUS


def convert_single_coordinate_pair(bounds, to_espg, lat, lon):
    min_x, min_y, max_x, max_y = bounds
    coordinate_pair = cor_to_crs(to_espg, lat, lon)
    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()
    lat_scaled = (polar_lat - min_x) / (max_x - min_x)
    lon_scaled = (polar_lon - min_y) / (max_y - min_y)
    return [lat_scaled, lon_scaled]


def convert_coordinates(raster, to_espg, lat, lon, only_height=False):
    b = raster.bounds
    min_x, min_y, max_x, max_y = b.left, b.bottom, b.right, b.top
    coordinate_pair = cor_to_crs(to_espg, lat, lon)
    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()

    resolution = raster.transform[0]
    lat_scaled = (polar_lat - min_x) / (max_x - min_x)
    lon_scaled = (polar_lon - min_y) / (max_y - min_y)

    to_crs = raster.crs
    from_crs = rasterio.crs.CRS.from_epsg(4326)
    new_x, new_y = reduce(operator.add, transform(from_crs, to_crs, [lon], [lat]))
    row, col = raster.index(new_x, new_y)
    h = raster.read(1)

    try:
        height = h[row][col]
        if only_height:
            return height
    except IndexError:
        return

    def scale_height(height):
        return (height - h.min()) / ((raster.height * resolution) - h.min()) / 2.1

    height_scaled = scale_height(height)
    height_max_mountain_scaled = scale_height(h.max())

    return [
        lat_scaled,
        height_scaled,
        lon_scaled,
        height_max_mountain_scaled,
    ]


# lat/lon to coordinate reference system coordinates
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


def crs_to_cor(to_espg, lat, lon, ele):
    in_sr = osr.SpatialReference()
    in_sr.ImportFromEPSG(4326)
    out_sr = osr.SpatialReference()
    out_sr.ImportFromEPSG(to_espg)
    coordinate_pair = ogr.Geometry(ogr.wkbPoint)
    coordinate_pair.AddPoint(lat, lon)
    coordinate_pair.AssignSpatialReference(out_sr)
    coordinate_pair.TransformTo(in_sr)
    lat = coordinate_pair.GetX()
    lon = coordinate_pair.GetY()
    return Location(latitude=float(lat), longitude=float(lon), elevation=ele)


def crs_to_wgs84(dataset, x, y):
    crs = rasterio.crs.CRS.from_epsg(4326)
    lon, lat = transform(dataset.crs, crs, xs=[x], ys=[y])
    return (lat, lon)


def look_at_location(in_lat, in_lon, dist_in_kms, true_course):
    bearing = radians(true_course)
    d = dist_in_kms
    lat1, lon1 = radians(in_lat), radians(in_lon)
    lat2 = asin(
        sin(lat1) * cos(d / EARTH_RADIUS)
        + cos(lat1) * sin(d / EARTH_RADIUS) * cos(bearing)
    )
    lon2 = lon1 + atan2(
        sin(bearing) * sin(d / EARTH_RADIUS) * cos(lat1),
        cos(d / EARTH_RADIUS) - sin(lat1) * sin(lat2),
    )
    lat2, lon2 = degrees(lat2), degrees(lon2)
    return lat2, lon2


def to_latlon(x, y, ds_raster):
    latitude, longitude = crs_to_wgs84(ds_raster, x, y)
    return (float(str(latitude).strip("[]")), float(str(longitude).strip("[]")))


def dms_to_decimal_degrees(coordinate):
    d, m, s = coordinate
    return d + (m / 60.0) + (s / 3600.0)
