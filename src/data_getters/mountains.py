import json


def get_mountain_data(json_path, filename):
    with open(json_path) as json_file:
        data = json.load(json_file)
        dem_file = data['dem-path']
        camera_mountain = data['panoramas']['%s_camera' % filename]
        look_at_mountain = data['panoramas']['%s_view' % filename]
        camera_lat, camera_lon = camera_mountain['latitude'], \
            camera_mountain['longitude']
        panoramic_angle = camera_mountain['panoramic_angle']
        height_field_scale_factor = camera_mountain['height_scale_factor']
        look_at_lat, look_at_lon = look_at_mountain['latitude'], \
            look_at_mountain['longitude']
        coordinates = [camera_lat, camera_lon, look_at_lat, look_at_lon]
        pov_settings = [panoramic_angle, height_field_scale_factor]
        return [dem_file, coordinates, pov_settings]


def get_mountain_list(json_path):
    with open(json_path) as json_file:
        data = json.load(json_file)
        return data['mountains']
