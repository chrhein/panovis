import sys
from pov_gen import panorama_creator


if __name__ == '__main__':
    lat, lon = 60.36458, 5.32426
    try:
        panorama_creator(sys.argv[1], lat, lon)
    except IndexError:
        demo = "tmp_geotiff.png"
        panorama_creator(demo, lat, lon)
        # print('Must provide .png, .dem or .tif file as argument')
