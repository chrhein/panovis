import sys
from src.pov_generator import panorama_creator


if __name__ == '__main__':
    camera_lat, camera_lon = 60.3609, 5.3191
    lookat_lat, lookat_lon = 60.46461, 5.29138
    try:
        panorama_creator(sys.argv[1], camera_lat, camera_lon, lookat_lat, lookat_lon)
    except IndexError:
        print('Must provide .png, .dem or .tif file as argument')
