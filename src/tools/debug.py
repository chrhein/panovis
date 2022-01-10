import cv2
import numpy as np
from osgeo import gdal


def p_i(text, same_line=False):
    if same_line:
        print(f"\r[INFO] {text}", end="", flush=True)
    else:
        print(f"[INFO] {text}")


def p_e(text):
    print("[ERROR] %s" % text)


def p_s(text):
    print("[SUCCESS] %s" % text)


def p_a(text):
    print("[ALERT] %s" % text)


def p_in(text):
    return input("[INPUT] %s" % text)


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
    p_i("Map coordinate for max height:")
    print(np.where(dem_array == dem_array.max()))
    p_i("Map coordinate for min height:")
    print(np.where(dem_array == dem_array.min()))
    p_i("Input file: %s" % in_dem)
    p_i("Camera position: %s, %s" % (lat, lon))
    p_i("Look at position: %s, %s" % (view_lat, view_lon))


def get_dataset_bounds(in_dem):
    dem_data = gdal.Open(in_dem)
    dem_array = np.array(dem_data.GetRasterBand(1).ReadAsArray())
    return [len(dem_array), len(dem_array[0])]


def nothing(x):
    pass


def custom_imshow(image, title, from_left=100, from_top=400):
    if type(image) == str:
        image = cv2.imread(image)
    cv2.namedWindow(title)
    cv2.moveWindow(title, from_left, from_top)
    cv2.imshow(title, image)
    cv2.setWindowProperty(title, cv2.WND_PROP_TOPMOST, 1)
    key_pressed = cv2.waitKey()
    cv2.destroyAllWindows()
    if key_pressed == 115:
        return True
    return False


def check_file_type(in_file):
    f = in_file.lower()
    allowed_file_types = [".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"]
    file_type = f[f.rfind(".") :]
    if file_type in allowed_file_types:
        return True
    else:
        return False
