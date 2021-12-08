from math import radians, asin, cos, sin, atan2, degrees, pi
import numpy as np
import rasterio
from osgeo import ogr, osr
from rasterio.warp import transform
from tools.debug import p_i, p_e
from colors import color_interpolator
from dotenv import load_dotenv
import folium
import os
from tools.types import Location
from geopy import distance


# constants
EARTH_RADIUS = 6378.1


def get_raster_data(dem_file, coordinates):
    ds_raster = rasterio.open(dem_file)
    # get resolution (points per square meter)
    resolution = ds_raster.transform[0]
    # get coordinate reference system
    crs = int(ds_raster.crs.to_authority()[1])
    # convert lat_lon to grid coordinates in the interval [0, 1]
    camera_lat_lon = convert_coordinates(ds_raster, crs, coordinates[0], coordinates[1])
    if not camera_lat_lon:
        p_e("Camera location is out of bounds")
        return
    look_at_lat_lon = convert_coordinates(
        ds_raster, crs, coordinates[2], coordinates[3]
    )
    if not look_at_lat_lon:
        p_e("Viewpoint location is out of bounds")
        return
    raster_left, raster_bottom, raster_right, raster_top = ds_raster.bounds
    # get total sample points across x and y axis
    total_distance_e_w = raster_right - raster_left
    total_distance_n_s = raster_top - raster_bottom
    distances = [total_distance_n_s, total_distance_e_w]
    try:
        max_height = camera_lat_lon[-1]
    except TypeError:
        pass
    normalized_coordinates = [*camera_lat_lon[:3], *look_at_lat_lon[:3]]
    raster_metadata = [ds_raster, distances, resolution, max_height]
    return [normalized_coordinates, raster_metadata]


def get_location(lat, lon, hgt, look_at_lat, look_at_lon, look_at_hgt):
    return [[lat, lon, hgt], [look_at_lat, look_at_lon, look_at_hgt]]


def convert_single_coordinate_pair(bounds, to_espg, lat, lon):
    min_x, min_y, max_x, max_y = bounds
    coordinate_pair = cor_to_crs(to_espg, lat, lon)
    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()
    lat_scaled = (polar_lat - min_x) / (max_x - min_x)
    lon_scaled = (polar_lon - min_y) / (max_y - min_y)
    return [lat_scaled, lon_scaled]


def convert_coordinates(raster, to_espg, lat, lon):
    b = raster.bounds
    min_x, min_y, max_x, max_y = b.left, b.bottom, b.right, b.top
    coordinate_pair = cor_to_crs(to_espg, lat, lon)
    polar_lat = coordinate_pair.GetX()
    polar_lon = coordinate_pair.GetY()

    ds_height = max((max_x - min_x), (max_y - min_y))
    lat_scaled = (polar_lat - min_x) / (max_x - min_x)
    lon_scaled = (polar_lon - min_y) / (max_y - min_y)

    to_crs = raster.crs
    from_crs = rasterio.crs.CRS.from_epsg(4326)
    new_x, new_y = transform(from_crs, to_crs, [lon], [lat])
    new_x = new_x[0]
    new_y = new_y[0]
    row, col = raster.index(new_x, new_y)
    h = raster.read(1)

    try:
        height = h[row][col]
    except IndexError:
        return
    height_scaled = (height + 1.8) / ds_height
    height_max_mountain_scaled = h.max() / ds_height

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
    return lat, lon


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


def coordinate_lookup(im1, im2, dem_file):
    p_i("Searching for locations in image")
    ds = rasterio.open(dem_file)
    h1, w1, _ = im1.shape
    x_int_c = color_interpolator(255, 0, 255)
    y_int_c = color_interpolator(0, 255, 255)
    locs = set(
        to_latlon(im2[i, j], im1[i, j], x_int_c, y_int_c, ds)
        for i in range(0, h1, 10)
        for j in range(0, w1, 10)
        if im2[i, j][1] != 255
    )
    p_i("Search complete.")
    return locs


def plot_to_map(
    mountains_in_sight, coordinates, filename, locs=[], custom_color="darkblue"
):
    c_lat, c_lon, _, _ = coordinates
    load_dotenv()
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
    MAPBOX_STYLE_URL = os.getenv("MAPBOX_STYLE_URL")
    m = folium.Map(
        location=[c_lat, c_lon],
        tiles=MAPBOX_STYLE_URL,
        API_key=MAPBOX_TOKEN,
        zoom_start=12,
        attr="Christian Hein",
    )
    folium.Marker(
        location=[c_lat, c_lon],
        popup="Camera Location",
        icon=folium.Icon(color="green", icon="camera"),
    ).add_to(m)
    if locs:
        [
            (
                folium.Marker(
                    location=(float(i.latitude), float(i.longitude)),
                    popup="%s" % str(i).strip("()"),
                    icon=folium.Icon(color=custom_color, icon="mountain"),
                ).add_to(m)
            )
            for i in locs
        ]
    [
        (
            folium.Marker(
                location=(float(i.location.latitude), float(i.location.longitude)),
                popup="%s\n%.4f, %.4f\n%im"
                % (
                    str(i.name),
                    i.location.latitude,
                    i.location.longitude,
                    i.location.elevation,
                ),
                icon=folium.Icon(color="pink", icon="mountain"),
            ).add_to(m)
        )
        for i in mountains_in_sight.values()
    ]
    m.save(filename)


def get_mountains_in_sight(locs, mountains):
    mountains_in_sight = dict()
    radius = 500
    p_i("Finding mountains in sight with a %i meter radius" % radius)
    l_ = len(locs)
    div = 1
    for i in range(0, l_, div):
        pos = locs[i]
        lat, lon = pos.latitude, pos.longitude
        for mountain in mountains:
            m = mountain.location
            m_lat, m_lon = m.latitude, m.longitude
            center_point = [{"lat": m_lat, "lng": m_lon}]
            test_point = [{"lat": lat, "lng": lon}]
            center_point = tuple(center_point[0].values())
            test_point = tuple(test_point[0].values())
            dis = distance.distance(center_point, test_point).m
            if dis <= radius:
                mountains_in_sight[mountain.name] = mountain
    return mountains_in_sight


def displace_camera(camera_lat, camera_lon, degrees, distance):
    delta = distance / EARTH_RADIUS

    def to_radians(theta):
        return np.dot(theta, np.pi) / np.float32(180.0)

    def to_degrees(theta):
        return np.dot(theta, np.float32(180.0)) / np.pi

    degrees = to_radians(degrees)
    camera_lat = to_radians(camera_lat)
    camera_lon = to_radians(camera_lon)

    displaced_lat = asin(
        sin(camera_lat) * cos(delta) + cos(camera_lat) * sin(delta) * cos(degrees)
    )
    displaced_lon = camera_lon + atan2(
        sin(degrees) * sin(delta) * cos(camera_lat),
        cos(delta) - sin(camera_lat) * sin(displaced_lat),
    )
    displaced_lon = (displaced_lon + 3 * pi) % (2 * pi) - pi
    return to_degrees(displaced_lat), to_degrees(displaced_lon)
