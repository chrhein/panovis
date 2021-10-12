import cv2
import numpy as np
import rasterio
from math import ceil
from data_getters.mountains import read_gpx
from location_handler import convert_single_coordinate_pair

# stolen from
# https://www.cocyer.com/python-pillow-generate-gradient-image-with-numpy/


def get_gradient_2d(start, stop, width, height, is_horizontal):
    if is_horizontal:
        return np.tile(np.linspace(start, stop, width), (height, 1))
    else:
        return np.tile(np.linspace(start, stop, height), (width, 1)).T


def get_gradient_3d(width, height, start_list, stop_list, is_horizontal_list):
    result = np.zeros((height, width, len(start_list)), dtype=np.float)

    for i, (start, stop, is_horizontal) in enumerate(zip(start_list,
                                                         stop_list,
                                                         is_horizontal_list)):
        result[:, :, i] = get_gradient_2d(start, stop,
                                          width, height, is_horizontal)
    return result


def create_color_gradient_image():
    dem = './data/hordaland.png'
    im = cv2.imread(dem)
    h, w, _ = im.shape
    upper_left_color = (0, 0, 192)
    lower_right_color = (255, 255, 64)
    array = get_gradient_3d(w, h, upper_left_color, lower_right_color,
                            (True, False, False))

    img = cv2.cvtColor(np.uint8(array), cv2.COLOR_RGB2BGR)
    cv2.imwrite('data/color_gradient.png', img)


def create_hike_path_image(dem_file, gpx_path):
    im = cv2.imread(dem_file)
    h, w, c = im.shape
    mns = read_gpx(gpx_path)
    img = np.zeros([h, w, 4], dtype=np.uint8)
    """
    tmp = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, alpha = cv2.threshold(tmp, 0, 255, cv2.THRESH_BINARY)
    b, g, r = cv2.split(img)
    rgba = [b, g, r, alpha]
    dst = cv2.merge(rgba, 4)
    """
    ds_raster = rasterio.open(dem_file)

    crs = int(ds_raster.crs.to_authority()[1])
    b = ds_raster.bounds
    bounds = [b.left, b.bottom, b.right, b.top]
    locs = [convert_single_coordinate_pair(bounds, crs,
            i.latitude, i.longitude) for i in mns]
    for i in locs:
        lat, lon = i
        x = ceil(((100.0 * lat) / 100) * w)
        y = ceil(100-((100.0 * lon) / 100) * h)
        img[y][x] = (0, 0, 255, 255)

    filename = gpx_path.split('/')[-1].split('.')[0]
    im_path = 'exports/%s/%s_texture.png' % (filename, filename)
    cv2.imwrite(im_path, img)
    return im_path
