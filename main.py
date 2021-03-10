import sys
from pov_gen import panorama_creator


if __name__ == '__main__':
    try:
        panorama_creator(sys.argv[1])
    except IndexError:
        print('Must provide .png, .dem or .tif file as argument')
