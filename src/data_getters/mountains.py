import json
import gpxpy
import gpxpy.gpx
from location_handler import displace_camera
from debug_tools import p_i, p_line
from tools.file_handling import get_files, tui_select
from tools.types import Location, Mountain
from operator import attrgetter


def get_mountain_data(json_path, filename):
    with open(json_path) as json_file:
        data = json.load(json_file)
        dem_file = data['dem-path']
        camera_mountain = data['panoramas']['%s_camera' % filename]
        camera_lat, camera_lon = camera_mountain['latitude'], \
            camera_mountain['longitude']
        displacement_distance = 0.1  # in kms
        panoramic_angle = camera_mountain['panoramic_angle']
        height_field_scale_factor = camera_mountain['height_scale_factor']
        v_dir = camera_mountain['view_direction']
        look_ats = displace_camera(camera_lat,
                                   camera_lon,
                                   v_dir,
                                   displacement_distance)
        coordinates = [camera_lat, camera_lon, *look_ats]
        pov_settings = [panoramic_angle, height_field_scale_factor]
        return [dem_file, coordinates, pov_settings]


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
    mountain_dataset = {}
    info_title = 'Select one of these files to continue:'
    input_text = 'Select file: '
    error_text = 'No valid file chosen.'
    for i in range(len(files_in_folder)):
        file = files_in_folder[i].split('/')[-1]
        number_of_mountains_in_set = int(file.split('--')[0])
        mountain_name = file.split('--')[1].split('.')[0]
        mountain_dataset[mountain_name] = {
            'number_of_mountains': number_of_mountains_in_set,
            'file_name': files_in_folder[i]
        }
    mountain_dataset = dict(sorted(mountain_dataset.items(),
                            key=lambda item: item[1].get('number_of_mountains')))
    info_text = ['%s, size: %i' % (i, j['number_of_mountains']) for (i, j) in mountain_dataset.items()]
    selected_file = tui_select(info_text, info_title, input_text, error_text)
    dataset = tuple(mountain_dataset.items())[selected_file - 1][1]['file_name']
    p_i('%s was selected' % dataset.split('/')[-1])
    ds = {
        dataset: {
            'mountains': read_mountain_gpx(dataset)
        }
    }
    return ds


def compare_two_mountain_lists():
    folder = 'data/mountains/'
    mtns_1 = get_mountains(folder)
    mtns_2 = get_mountains(folder)
    mn1 = list(mtns_1.values())[0]['mountains']
    mn2 = list(mtns_2.values())[0]['mountains']
    mtns_un_1 = sorted([i for i in mn1 if i not in mn2], key=lambda n: n.name)
    mtns_un_2 = sorted([i for i in mn2 if i not in mn1], key=lambda n: n.name)

    ds = {
        list(mtns_1.keys())[0]: mtns_un_1,
        list(mtns_2.keys())[0]: mtns_un_2
    }

    for key, val in ds.items():
        print('\nMoutains unique to the following dataset:')
        print('%s:' % key.split('/')[-1])
        p_line(['%s' % i.name for i in val])
        break
