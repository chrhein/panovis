from math import asin, cos, radians, sin, atan2, degrees, pi
import numpy as np
import rasterio
from tools.converters import (
    convert_coordinates,
    crs_to_cor,
    crs_to_wgs84,
    get_earth_radius,
)
from tools.debug import p_i, p_e, p_line, p_s
from geopy import distance
from alive_progress import alive_bar
from pygeodesy.sphericalNvector import LatLon
from numpy import arctan2, sin, cos, degrees
import cv2
from operator import attrgetter

from tools.types import Location, Location3D


def get_raster_data(dem_file, coordinates):
    ds_raster = rasterio.open(dem_file)
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
    raster_metadata = [ds_raster, distances, max_height]
    return [normalized_coordinates, raster_metadata]


def get_location(lat, lon, hgt, look_at_lat, look_at_lon, look_at_hgt):
    return [[lat, lon, hgt], [look_at_lat, look_at_lon, look_at_hgt]]


def find_visible_coordinates_in_render(ds_name, gradient_path, render_path, dem_file):
    render_with_gradient = f"{ds_name}-render-gradient.png"
    p_i(f"Finding all visible coordinates in {render_with_gradient}")
    image = cv2.cvtColor(cv2.imread(render_path), cv2.COLOR_BGR2RGB)
    p_i("Computing list of unique colors")
    unique_colors = np.unique(image.reshape(-1, image.shape[2]), axis=0)[2:]

    p_i("Getting pixel coordinates for colors in render")
    g = cv2.cvtColor(cv2.imread(gradient_path), cv2.COLOR_BGR2RGB)
    color_coordinates = [np.where(np.all(g == i, axis=-1)) for i in unique_colors]
    color_coordinates = [(i[0][0], i[1][0]) for i in color_coordinates if len(i[0]) > 0]

    latlon_color_coordinates = []
    ds_raster = rasterio.open(dem_file)
    ds_raster_height_band = ds_raster.read(1)
    crs = int(ds_raster.crs.to_authority()[1])
    dims = ds_raster_height_band.shape

    x_ = dims[0] / (2 ** 8)
    y_ = dims[1] / (2 ** 8)

    for x, y in color_coordinates:
        s_x, s_y = round(x * x_), round(y * y_)
        px, py = ds_raster.xy(s_x, s_y)
        height = ds_raster_height_band[s_x, s_y]
        latlon_color_coordinates.append(crs_to_cor(crs, px, py, height))
    return latlon_color_coordinates


def get_mountains_in_sight(dem_file, locs, mountains, radius=150):
    p_i("Looking for mountains in sight:")
    lower_left, upper_left, upper_right, lower_right = get_raster_bounds(dem_file)
    b = (
        LatLon(*lower_left),
        LatLon(*upper_left),
        LatLon(*upper_right),
        LatLon(*lower_right),
    )
    filtered_mountains = []
    for m in mountains:
        loc = m.location
        p = LatLon(loc.latitude, loc.longitude)
        if p.isenclosedBy(b):
            filtered_mountains.append(m)

    mountains_in_sight = {}
    min_mountain_height = min([i.location.elevation for i in filtered_mountains])

    copied_locs = [i for i in locs if i.elevation >= min_mountain_height]
    p_line(
        [
            f"Total number of locations:     {len(locs)}",
            f"Total number of mountains:     {len(mountains)}",
            f"Number of locations in search: {len(copied_locs)}",
            f"Number of mountains in search: {len(filtered_mountains)}",
        ]
    )
    with alive_bar(len(filtered_mountains)) as bar:
        for mountain in filtered_mountains:
            for loc in copied_locs:
                if loc_close_to_mountain(loc, mountain.location, radius):
                    mountains_in_sight[mountain.name] = mountain
                    copied_locs.remove(loc)
                    break
            bar()

    if len(mountains_in_sight) == 0:
        p_e("No mountains in sight")
    else:
        p_s(f"Found a total of {len(mountains_in_sight)} mountains in sight")
        print(mountains_in_sight)
    return mountains_in_sight


def loc_close_to_mountain(loc, m, radius):
    mountain_pos = tuple([{"lat": m.latitude, "lng": m.longitude}][0].values())
    test_loc = tuple([{"lat": loc.latitude, "lng": loc.longitude}][0].values())
    return distance.distance(mountain_pos, test_loc).m <= radius


def displace_camera(camera_lat, camera_lon, deg=0.0, distance=0.1):
    delta = distance / get_earth_radius()

    def to_radians(theta):
        return np.dot(theta, np.pi) / np.float32(180.0)

    def to_degrees(theta):
        return np.dot(theta, np.float32(180.0)) / np.pi

    deg = to_radians(deg)
    camera_lat = to_radians(camera_lat)
    camera_lon = to_radians(camera_lon)

    displaced_lat = asin(
        sin(camera_lat) * cos(delta) + cos(camera_lat) * sin(delta) * cos(deg)
    )
    displaced_lon = camera_lon + atan2(
        sin(deg) * sin(delta) * cos(camera_lat),
        cos(delta) - sin(camera_lat) * sin(displaced_lat),
    )
    displaced_lon = (displaced_lon + 3 * pi) % (2 * pi) - pi
    return to_degrees(displaced_lat), to_degrees(displaced_lon)


def get_min_max_coordinates(dem_file):
    lower_left, _, upper_right, _ = get_raster_bounds(dem_file)
    return lower_left + upper_right


def get_raster_bounds(dem_file, lat_lon=True):
    ds_raster = rasterio.open(dem_file)
    bounds = ds_raster.bounds

    def format_coords(coords):
        return [c[0] for c in coords]

    if lat_lon:
        lower_left = format_coords(crs_to_wgs84(ds_raster, bounds.left, bounds.bottom))
        upper_left = format_coords(crs_to_wgs84(ds_raster, bounds.left, bounds.top))
        upper_right = format_coords(crs_to_wgs84(ds_raster, bounds.right, bounds.top))
        lower_right = format_coords(
            crs_to_wgs84(ds_raster, bounds.right, bounds.bottom)
        )
    else:
        lower_left = (bounds.left, bounds.bottom)
        upper_left = (bounds.left, bounds.top)
        upper_right = (bounds.right, bounds.top)
        lower_right = (bounds.right, bounds.bottom)

    return lower_left, upper_left, upper_right, lower_right


def get_bearing(lat1, lon1, lat2, lon2):
    dL = lon2 - lon1
    X = cos(lat2) * sin(dL)
    Y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(dL)
    bearing = arctan2(X, Y)
    return degrees(bearing)


def find_minimums(locations):
    min_lat = min(locations, key=attrgetter("latitude"))
    min_lon = min(locations, key=attrgetter("longitude"))
    return [min_lat, min_lon]


def find_maximums(locations):
    max_lat = max(locations, key=attrgetter("latitude"))
    max_lon = max(locations, key=attrgetter("longitude"))
    return [max_lat, max_lon]


def get_fov_bounds(total_width, left_bound, right_bound):
    def convert_to_degrees(x):
        return (x * 360 / total_width) % 360

    left_bound = convert_to_degrees(left_bound)
    right_bound = convert_to_degrees(right_bound)
    return (left_bound, right_bound)


def get_fov(fov):
    left_bound, right_bound = fov
    return (right_bound - left_bound) % 360


def get_view_direction(fov):
    left_bound, _ = fov
    fov_deg = get_fov(fov)
    return ((left_bound + (fov_deg / 2)) + 180) % 360


def get_distance_between_locations(loc1, loc2):
    return distance.distance(
        (loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)
    ).m


def find_angle_between_three_locations(loc1, loc2, loc3):
    return get_bearing(
        loc1.latitude, loc1.longitude, loc2.latitude, loc2.longitude
    ) - get_bearing(loc1.latitude, loc1.longitude, loc3.latitude, loc3.longitude)


def get_mountain_3d_location(camera_location, viewing_direction, mountains):
    loc2 = camera_location
    for mountain in mountains.values():
        d = get_distance_between_locations(camera_location, mountain.location)
        c_e = camera_location.elevation
        m_e = mountain.location.elevation
        diff = m_e - c_e
        h = (d ** 2 + diff ** 2) ** 0.5
        ang = degrees(asin(diff / h))

        loc3 = mountain.location
        # deg = find_angle_between_three_locations(loc1, loc2, loc3)
        deg = get_bearing(loc3.latitude, loc3.longitude, loc2.latitude, loc2.longitude)

        mountain.set_location_in_3d(Location3D(yaw=deg, pitch=ang, distance=d))

    return mountains
