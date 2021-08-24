import json

def get_mountain_data(json_path):
    with open(json_path) as json_file:
        data = json.load(json_file)
        file = data['dem-path']
        camera_mountain = data['mountains']['strandafjellet']
        look_at_mountain = data['mountains']['ulriken']
        camera_lat, camera_lon = camera_mountain['latitude'], camera_mountain['longitude']
        look_at_lat, look_at_lon = look_at_mountain['latitude'], look_at_mountain['longitude']
        return [file, camera_lat, camera_lon, look_at_lat, look_at_lon]