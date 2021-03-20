import sys
from src.pov_generator import panorama_creator


if __name__ == '__main__':
    camera_lat, camera_lon = 60.3775, 5.3871
    lookat_lat, lookat_lon = 60.36458, 5.32426
    try:
        panorama_creator(sys.argv[1], camera_lat, camera_lon, lookat_lat, lookat_lon)
    except IndexError:
        print('Must provide .png, .dem or .tif file as argument')
