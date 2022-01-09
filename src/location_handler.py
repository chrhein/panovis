from math import radians, asin, cos, sin, atan2, degrees, pi
import numpy as np
import rasterio
from osgeo import ogr, osr, gdal
from rasterio.warp import transform
from tools.debug import p_i, p_e, p_s
from dotenv import load_dotenv
import folium, folium.raster_layers
import os
from tools.types import Location
from geopy import distance
from functools import reduce
import operator
from alive_progress import alive_bar
from pygeodesy.sphericalNvector import LatLon
import cv2

# constants
EARTH_RADIUS = 6378.1


def get_raster_data(dem_file, coordinates):
    ds_raster = rasterio.open(dem_file)
    # plot_to_map(None, coordinates, "dev/test_map.html", dem_file)
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


def plot_to_map(
    mountains_in_sight,
    coordinates,
    filename,
    dem_file,
    locs=[],
    mountains=[],
    mountain_radius=150,
):
    p_i("Creating Interactive Map")
    c_lat, c_lon, _, _ = coordinates
    ll, ul, ur, lr = get_raster_bounds(dem_file)
    load_dotenv()
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
    MAPBOX_STYLE_URL = os.getenv("MAPBOX_STYLE_URL")
    m = folium.Map([c_lat, c_lon], tiles=None, zoom_start=12)
    folium.TileLayer(
        location=[c_lat, c_lon],
        tiles=MAPBOX_STYLE_URL,
        API_key=MAPBOX_TOKEN,
        attr="Christian Hein",
        name="Map",
    ).add_to(m)

    raster_bounds = folium.FeatureGroup(name="Raster Bounds", show=True)
    m.add_child(raster_bounds)
    folium.PolyLine(locations=[ll, ul, ur, lr, ll], color="#ed6952").add_to(
        raster_bounds
    )

    folium.Marker(
        location=[c_lat, c_lon],
        popup="Camera Location",
        icon=folium.Icon(color="green", icon="camera"),
    ).add_to(m)

    color_gradient = folium.FeatureGroup(
        name="Color Gradient (Not Working)", show=False
    )
    m.add_child(color_gradient)
    im = cv2.cvtColor(cv2.imread("data/color_gradient.png"), cv2.COLOR_BGR2RGB)
    folium.raster_layers.ImageOverlay(
        image=im,
        bounds=[ll, ur],
        mercator_project=True,
        origin="upper",
    ).add_to(color_gradient)

    if locs:
        locs_fg = folium.FeatureGroup(name="Retrieved Coordinates", show=False)
        m.add_child(locs_fg)
        [
            (
                folium.Circle(
                    location=(i.latitude, i.longitude),
                    color="#0a6496",
                    fill=True,
                    fill_color="#0a6496",
                    fill_opacity=1,
                    radius=15,
                ).add_to(locs_fg)
            )
            for i in locs
        ]
    if mountains:
        mountains_fg = folium.FeatureGroup(name="All Mountains", show=False)
        m.add_child(mountains_fg)
        [
            (
                folium.Circle(
                    location=(i.location.latitude, i.location.longitude),
                    color="#ed6952",
                    fill=True,
                    fill_color="#ed6952",
                    fill_opacity=0.2,
                    radius=mountain_radius,
                    popup=f"{i.name}, {int(i.location.elevation)} m",
                ).add_to(mountains_fg)
            )
            for i in mountains
        ]
    if mountains_in_sight:
        mountains_in_sight_fg = folium.FeatureGroup(
            name="Mountains In-Sight", show=True
        )
        m.add_child(mountains_in_sight_fg)
        [
            (
                folium.Marker(
                    location=(i.location.latitude, i.location.longitude),
                    popup="%s\n%.4f, %.4f\n%im"
                    % (
                        str(i.name),
                        i.location.latitude,
                        i.location.longitude,
                        i.location.elevation,
                    ),
                    icon=folium.Icon(color="pink", icon="mountain"),
                ).add_to(mountains_in_sight_fg)
            )
            for i in mountains_in_sight.values()
        ]
    folium.LayerControl().add_to(m)
    m.save(filename)


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
    max_mountain_height = max([i.location.elevation for i in filtered_mountains])

    copied_locs = [
        i
        for i in locs
        if i.elevation >= min_mountain_height and i.elevation <= max_mountain_height
    ]
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
    return mountains_in_sight


def loc_close_to_mountain(loc, m, radius):
    mountain_pos = tuple([{"lat": m.latitude, "lng": m.longitude}][0].values())
    test_loc = tuple([{"lat": loc.latitude, "lng": loc.longitude}][0].values())
    return distance.distance(mountain_pos, test_loc).m <= radius


def displace_camera(camera_lat, camera_lon, degrees=0.0, distance=0.1):
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


def get_min_max_coordinates(dem_file):
    lower_left, _, upper_right, _ = get_raster_bounds(dem_file)
    return lower_left + upper_right


def get_raster_bounds(dem_file):
    ds_raster = rasterio.open(dem_file)
    bounds = ds_raster.bounds

    def format_coords(coords):
        return [c[0] for c in coords]

    lower_left = format_coords(crs_to_wgs84(ds_raster, bounds.left, bounds.bottom))
    upper_left = format_coords(crs_to_wgs84(ds_raster, bounds.left, bounds.top))
    upper_right = format_coords(crs_to_wgs84(ds_raster, bounds.right, bounds.top))
    lower_right = format_coords(crs_to_wgs84(ds_raster, bounds.right, bounds.bottom))

    return lower_left, upper_left, upper_right, lower_right
