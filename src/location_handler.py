from json import load
from math import asin, atan2, pi, sqrt
import numpy as np
import rasterio
from tools.converters import (
    convert_coordinates,
    get_earth_radius,
)
from tools.debug import p_a, p_e, p_s
from numpy import arctan2, sin, cos, degrees
import cv2
from operator import attrgetter
from tools.types import CrsToLatLng, Distance, LatLngToCrs, Location3D
from osgeo import gdal


def get_raster_data(ds_raster, coordinates):
    crs = int(ds_raster.crs.to_authority()[1])
    converter = LatLngToCrs(crs)
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
    total_distance_e_w = raster_right - raster_left
    total_distance_n_s = raster_top - raster_bottom
    distances = [total_distance_n_s, total_distance_e_w]
    try:
        max_height = camera_lat_lon[-1]
    except TypeError:
        max_height = 10000
        pass
    normalized_coordinates = [*camera_lat_lon[:3], *look_at_lat_lon[:3]]
    raster_metadata = [distances, max_height]
    return [normalized_coordinates, raster_metadata]


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


def get_visible_coordinates(ds_raster, viewshed):
    im = cv2.imread(viewshed, cv2.IMREAD_GRAYSCALE)
    coords = np.column_stack(np.where(im == 255))
    height_band = ds_raster.read(1)
    return [ds_raster.xy(*xy) for xy in coords if height_band[coords[0], coords[1]] > 25]


def find_visible_items_in_ds(ds_viewshed, dataset):
    if len(dataset) == 0:
        return []

    items_in_sight = set()
    vs_val = ds_viewshed.read(1)

    for i in dataset:
        try:
            for x in range(-1, 2):
                for y in range(-1, 2):
                    loc = i.location2d
                    raster_coordinates = ds_viewshed.index(loc[0]+x, loc[1]+y)
                    if vs_val[raster_coordinates] == 255:
                        if i not in items_in_sight:
                            items_in_sight.add(i)
                        break
        except IndexError:
            continue

    if len(items_in_sight) == 0:
        p_a("No items in sight")
    else:
        p_s(f"Found a total of {len(items_in_sight)} items in sight")
    return items_in_sight


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
    loc3 = converter.convert(camera_location.latitude,
                             camera_location.longitude)

    def find_angle_between_three_locations(loc1, loc2, loc3):
        a1 = atan2(loc3.GetX() - loc2.GetX(), loc3.GetY() - loc2.GetY())
        a2 = atan2(loc3.GetX() - loc1.GetX(), loc3.GetY() - loc1.GetY())
        return degrees(a1 - a2)

    def get_3d_placement(loc1, loc3, camera_location, item, generator, converter):
        d = generator.get_distance_between_locations(
            camera_location, item.location)
        c_e = camera_location.elevation + 25
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


def create_viewshed(dem_file, location, folder):
    x, y = location
    viewshed_filename = f"{folder}/viewshed.tif"
    ds = gdal.Open(dem_file, gdal.GA_ReadOnly)
    band = ds.GetRasterBand(1)
    resolution = ds.GetGeoTransform()[1]
    max_dist = max(band.XSize * resolution, band.YSize * resolution)
    max_dist = sqrt((max_dist / 2) ** 2 + (max_dist / 2) ** 2)
    gdal.ViewshedGenerate(
        srcBand=band,
        driverName=ds.GetDriver().ShortName,
        targetRasterName=viewshed_filename,
        creationOptions=None,
        observerX=x,
        observerY=y,
        observerHeight=2,
        targetHeight=1.8,
        visibleVal=255,
        invisibleVal=0,
        outOfRangeVal=0,
        noDataVal=0,
        dfCurvCoeff=0.85714,
        mode=2,
        maxDistance=max_dist)
