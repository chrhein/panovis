import json
import gpxpy
import gpxpy.gpx
from location_handler import displace_camera
from tools.types import Location, Mountain
from operator import attrgetter


def get_mountain_data(json_path, filename):
    with open(json_path) as json_file:
        data = json.load(json_file)
        dem_file = data['dem-path']
        camera_mountain = data['panoramas']['%s_camera' % filename]
        camera_lat, camera_lon = camera_mountain['latitude'], \
            camera_mountain['longitude']
        displacement_distance = 1  # in kms
        panoramic_angle = camera_mountain['panoramic_angle']
        height_field_scale_factor = camera_mountain['height_scale_factor']
        look_at_lat, look_at_lon = displace_camera(camera_lat,
                                                   camera_lon,
                                                   camera_mountain['view_direction'],
                                                   displacement_distance)
        coordinates = [camera_lat, camera_lon, look_at_lat, look_at_lon]
        pov_settings = [panoramic_angle, height_field_scale_factor]
        return [dem_file, coordinates, pov_settings]


def get_mountain_list(json_path):
    with open(json_path) as json_file:
        data = json.load(json_file)
        m = data['mountains']
        mountains = [Mountain(m[i]['name'],
                     Location(m[i]['latitude'],
                     m[i]['longitude']))
                     for i in m]
        return mountains


def find_minimums(locations):
    min_lat = min(locations, key=attrgetter('latitude'))
    min_lon = min(locations, key=attrgetter('longitude'))
    return [min_lat, min_lon]


def find_maximums(locations):
    max_lat = max(locations, key=attrgetter('latitude'))
    max_lon = max(locations, key=attrgetter('longitude'))
    return [max_lat, max_lon]


def read_gpx(gpx_path):
    try:
        gpx_file = open(gpx_path, 'r')
    except FileNotFoundError:
        return []
    gpx = gpxpy.parse(gpx_file)
    locations = [Location(k.latitude, k.longitude, k.elevation)
                 for i in gpx.tracks
                 for j in i.segments
                 for k in j.points]
    return [locations, find_minimums(locations), find_maximums(locations)]
