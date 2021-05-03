import numpy as np
from osgeo import gdal


def p_i(text):
    print("[INFO]", text)


def p_e(text):
    print("[ERROR]", text)


def p_line(p_list):
    print("===================================================")
    for item in p_list:
        print(item)
    print("===================================================")


def dem_data_debugger(in_dem, lat, lon, view_lat, view_lon):
    dem_data = gdal.Open(in_dem)
    dem_array = np.array(dem_data.GetRasterBand(1).ReadAsArray())
    p_i('Map coordinate for max height:')
    print(np.where(dem_array == dem_array.max()))
    p_i('Map coordinate for min height:')
    print(np.where(dem_array == dem_array.min()))
    p_i('Input file: %s' % in_dem)
    p_i('Camera position: %s, %s' % (lat, lon))
    p_i('Look at position: %s, %s' % (view_lat, view_lon))


def nothing(x):
    pass
