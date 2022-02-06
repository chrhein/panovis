from json import load
from math import asin, cos, sin, atan2, degrees, pi
import os
import pickle
import numpy as np
import rasterio
from tools.converters import (
    convert_coordinates,
    get_earth_radius,
)
from tools.debug import p_a, p_i, p_e, p_s
from pygeodesy.sphericalNvector import LatLon
from numpy import arctan2, sin, cos, degrees
import cv2
from operator import attrgetter
from tools.types import CrsToLatLng, Distance, LatLngToCrs, Location3D
from numba import njit


def get_raster_data(dem_file, coordinates):
    ds_raster = rasterio.open(dem_file)
    # get coordinate reference system
    crs = int(ds_raster.crs.to_authority()[1])
    converter = LatLngToCrs(crs)
    # convert lat_lon to grid coordinates in the interval [0, 1]
    camera_lat_lon = convert_coordinates(
        ds_raster, converter, coordinates[0], coordinates[1]
    )
    if not camera_lat_lon:
        p_e("Camera location is out of bounds")
        return
    look_at_lat_lon = convert_coordinates(
        ds_raster, converter, coordinates[2], coordinates[3]
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
        max_height = 10000
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
    color_coordinates_path = f"data/color_coords.pkl"
    if not os.path.exists(color_coordinates_path):
        g = cv2.cvtColor(cv2.imread(gradient_path), cv2.COLOR_BGR2RGB)
        color_coords = {}
        for y in range(g.shape[0]):
            for x in range(g.shape[1]):
                color_coords[tuple(g[x, y])] = (x, y)
        with open(color_coordinates_path, "wb") as f:
            pickle.dump(color_coords, f)
    else:
        with open(color_coordinates_path, "rb") as f:
            color_coords = pickle.load(f)

    ds_raster = rasterio.open(dem_file)
    ds_raster_height_band = ds_raster.read(1)
    dims = ds_raster_height_band.shape

    x_ = dims[0] / (256)
    y_ = dims[1] / (256)

    coords = []
    height_threshold = 50

    for color in unique_colors:
        c = color_coords.get(tuple(color))
        if c is not None:
            x, y = c
            s_x, s_y = round(x * x_), round(y * y_)
            px, py = ds_raster.xy(s_x, s_y)
            height = ds_raster_height_band[s_x, s_y]
            if height > height_threshold:
                coords.append(np.array((px, py)))
    return coords


def get_raster_path():
    render_settings_path = "render_settings.json"
    with open(render_settings_path) as json_file:
        data = load(json_file)
        dem_path = data["dem_path"]
    return dem_path


def get_height_from_raster(location, ds_raster, converter):
    h = convert_coordinates(
        ds_raster, converter, location.latitude, location.longitude, only_height=True
    )
    return h


def find_visible_items_in_ds(locs, dataset, radius=150):
    if len(dataset) == 0:
        return []
    lower_left, upper_left, upper_right, lower_right = get_raster_bounds(
        get_raster_path()
    )
    b = (
        LatLon(*lower_left),
        LatLon(*upper_left),
        LatLon(*upper_right),
        LatLon(*lower_right),
    )
    filtered_dataset = []
    for i in dataset:
        loc = i.location
        p = LatLon(loc.latitude, loc.longitude)
        if p.isenclosedBy(b):
            filtered_dataset.append(i)

    items_in_sight = []

    radius_sqrd = radius ** 2
    for i in filtered_dataset:
        for loc in locs:
            if euclidian_distance(loc, i.location2d, radius_sqrd):
                items_in_sight.append(i)
                break

    if len(items_in_sight) == 0:
        p_a("No items in sight")
    else:
        p_s(f"Found a total of {len(items_in_sight)} items in sight")
    return items_in_sight


@njit
def euclidian_distance(y1, y2, radius_sqrd):
    return np.sum((y1 - y2) ** 2) <= radius_sqrd


def displace_camera(camera_lat, camera_lon, deg=0.0, dist=0.1):
    delta = dist / get_earth_radius()

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
    crs = int(ds_raster.crs.to_authority()[1])

    converter = CrsToLatLng(crs)

    if lat_lon:
        ll = converter.convert(bounds.left, bounds.bottom)
        lower_left = ll.latitude, ll.longitude
        ul = converter.convert(bounds.left, bounds.top)
        upper_left = ul.latitude, ul.longitude
        ur = converter.convert(bounds.right, bounds.top)
        upper_right = ur.latitude, ur.longitude
        lr = converter.convert(bounds.right, bounds.bottom)
        lower_right = lr.latitude, lr.longitude
    else:
        lower_left = (bounds.left, bounds.bottom)
        upper_left = (bounds.left, bounds.top)
        upper_right = (bounds.right, bounds.top)
        lower_right = (bounds.right, bounds.bottom)

    return lower_left, upper_left, upper_right, lower_right


def get_bearing(lat1, lon1, lat2, lon2):
    d_l = lon2 - lon1
    x = cos(lat2) * sin(d_l)
    y = cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(d_l)
    bearing = arctan2(x, y)
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
    return left_bound, right_bound


def get_fov(fov):
    left_bound, right_bound = fov
    return (right_bound - left_bound) % 360


def get_view_direction(fov):
    left_bound, _ = fov
    fov_deg = get_fov(fov)
    return ((left_bound + (fov_deg / 2)) + 180) % 360


def get_3d_location(camera_location, viewing_direction, converter, dataset):
    loc1 = converter.convert(
        *displace_camera(
            camera_location.latitude,
            camera_location.longitude,
            deg=viewing_direction,
            dist=1.0,
        ),
    )
    loc3 = converter.convert(camera_location.latitude, camera_location.longitude)

    def find_angle_between_three_locations(loc1, loc2, loc3):
        a1 = atan2(loc3.GetX() - loc2.GetX(), loc3.GetY() - loc2.GetY())
        a2 = atan2(loc3.GetX() - loc1.GetX(), loc3.GetY() - loc1.GetY())
        return degrees(a1 - a2)

    def get_3d_placement(loc1, loc3, camera_location, item, generator, converter):
        d = generator.get_distance_between_locations(camera_location, item.location)
        c_e = camera_location.elevation + 15
        i_e = item.location.elevation
        diff = i_e - c_e
        h = (d ** 2 + diff ** 2) ** 0.5
        pitch = degrees(asin(diff / h))
        i = item.location
        loc2 = converter.convert(i.latitude, i.longitude)
        yaw = find_angle_between_three_locations(loc1, loc2, loc3)
        return yaw, pitch, d

    generator = Distance()
    for item in dataset:
        yaw, pitch, d = get_3d_placement(
            loc1, loc3, camera_location, item, generator, converter
        )
        item.set_location_in_3d(Location3D(yaw=yaw, pitch=pitch, distance=d))

    return dataset
