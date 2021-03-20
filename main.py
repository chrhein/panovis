import sys
from pov_generator import panorama_creator


if __name__ == '__main__':
    lat, lon = 60.36458, 5.32426
    try:
        panorama_creator(sys.argv[1], lat, lon)
    except IndexError:
        print('Must provide .png, .dem or .tif file as argument')
