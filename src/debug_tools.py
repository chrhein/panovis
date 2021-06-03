import cv2
import numpy as np
from osgeo import gdal


def p_i(text):
    print("[INFO]", text)


def p_e(text):
    print("[ERROR]", text)


def p_a(text):
    print("[ALERT]", text)


def p_line(p_list=[]):
    print("===================================================")
    if not p_list:
        return
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


def get_dataset_bounds(in_dem):
    dem_data = gdal.Open(in_dem)
    dem_array = np.array(dem_data.GetRasterBand(1).ReadAsArray())
    return [len(dem_array), len(dem_array[0])]


def custom_imshow(image, title, wait_key=1, from_left=100, from_top=400):
    cv2.namedWindow(title)
    cv2.moveWindow(title, from_left, from_top)
    cv2.imshow(title, image)
    cv2.setWindowProperty(title, cv2.WND_PROP_TOPMOST, 1)
    cv2.waitKey(0) if wait_key == 1 else nothing(0)


def nothing(x):
    pass