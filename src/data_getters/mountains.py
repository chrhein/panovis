import json
import gpxpy
import gpxpy.gpx
from location_handler import displace_camera
from debug_tools import p_line, p_i, p_in, p_e
from tools.file_handling import get_files
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


def read_hike_gpx(gpx_path):
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


def read_mountain_gpx(gpx_path):
    try:
        gpx_file = open(gpx_path, 'r')
    except FileNotFoundError:
        return []
    gpx = gpxpy.parse(gpx_file)
    mountains = [Mountain(i.name,
                 Location(i.latitude, i.longitude, i.elevation))
                 for i in gpx.waypoints]
    return mountains


def get_mountains(folder):
    files_in_folder = get_files(folder)
    info_text = []
    for i in range(len(files_in_folder)):
        file = files_in_folder[i].split('/')[-1]
        number_of_mountains_in_set = int(file.split('--')[0])
        mountain_name = file.split('--')[1].split('.')[0]
        info_text.append('%i: %s, size: %i' %
                         (i + 1, mountain_name,
                          number_of_mountains_in_set))
    p_i("Select one of these files to continue:")
    p_line(info_text)
    while True:
        try:
            selected_file = p_in("Select file: ")
            selected_file = int(selected_file)
        except ValueError:
            p_e('No valid file chosen.')
            continue
        if selected_file < 1 or selected_file > len(info_text):
            p_e('No valid file chosen.')
            continue
        dataset = files_in_folder[selected_file - 1]
        p_i('%s was selected' % dataset.split('/')[-1])
        break
    return read_mountain_gpx(dataset)
