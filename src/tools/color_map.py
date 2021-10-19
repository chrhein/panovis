import os
import cv2
import numpy as np
import rasterio
from data_getters.mountains import read_gpx
from location_handler import convert_single_coordinate_pair
import collections
import pickle
from tools.types import TextureBounds


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
    dem = './data/bergen.png'
    im = cv2.imread(dem)
    h, w, _ = im.shape
    upper_left_color = (0, 0, 192)
    lower_right_color = (255, 255, 64)
    array = get_gradient_3d(w, h, upper_left_color, lower_right_color,
                            (True, False, False))

    img = cv2.cvtColor(np.uint8(array), cv2.COLOR_RGB2BGR)
    cv2.imwrite('data/color_gradient.png', img)


def color_gradient_to_index():
    im = cv2.imread('data/color_gradient.png')
    h, w, _ = im.shape
    tbl = collections.defaultdict(list)
    for y in range(h):
        print(y)
        for x in range(w):
            tbl[str(im[y][x])].append([y, x])

    with open('data/color_gradient.pkl', 'wb') as f:
        pickle.dump(tbl, f)


def load_gradient():
    with open('data/color_gradient.pkl', 'rb') as f:
        return pickle.load(f)


def create_route_texture(dem_file, gpx_path, debugging=False):
    filename = gpx_path.split('/')[-1].split('.')[0]
    folder = 'exports/%s/texture' % filename
    if debugging:
        im_path = '%s/%s-texture-debug.png' % (folder, filename)
    else:
        im_path = '%s/%s-texture.png' % (folder, filename)
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    texture_bounds_path = '%s/%s-texture-bounds.pkl' % (folder, filename)
    texture_exist = os.path.isfile('%s' % im_path)
    bounds_exist = os.path.isfile('%s' % texture_bounds_path)
    if texture_exist and bounds_exist:
        with open(texture_bounds_path, 'rb') as f:
            tex_bounds = pickle.load(f)
        return [im_path, tex_bounds]
    im = cv2.imread(dem_file)
    h, w, _ = im.shape
    rs = 3
    if debugging:
        rs = 20

    multiplier = 10

    h = h * multiplier
    w = w * multiplier
    mns, minimums, maximums = read_gpx(gpx_path)
    if not mns:
        return ["", ""]
    img = np.ones([h, w, 4], dtype=np.uint8)
    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])
    b = ds_raster.bounds
    bounds = [b.left, b.bottom, b.right, b.top]
    locs = [convert_single_coordinate_pair(bounds, crs,
            i.latitude, i.longitude) for i in mns]
    prev_lat = abs(int(((100.0 * locs[0][0]) / 100) * w))
    prev_lon = h-abs(int(100.0-((100.0 * locs[0][1]) / 100.0) * h))
    for i in locs:
        lat, lon = i
        x = h-abs(int(100.0-((100.0 * lon) / 100.0) * h))
        y = abs(int(((100.0 * lat) / 100.0) * w))
        cv2.line(img, (prev_lat, prev_lon), (y, x), (0, 0, 255, 255), 3*rs)
        prev_lat, prev_lon = y, x
    min_lat_p = minimums[0]
    min_lon_p = minimums[1]
    max_lat_p = maximums[0]
    max_lon_p = maximums[1]
    min_x = convert_single_coordinate_pair(bounds, crs,
                                           min_lat_p.latitude,
                                           min_lat_p.longitude)
    min_y = convert_single_coordinate_pair(bounds, crs,
                                           min_lon_p.latitude,
                                           min_lon_p.longitude)
    max_x = convert_single_coordinate_pair(bounds, crs,
                                           max_lat_p.latitude,
                                           max_lat_p.longitude)
    max_y = convert_single_coordinate_pair(bounds, crs,
                                           max_lon_p.latitude,
                                           max_lon_p.longitude)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh,
                                   cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    cnt = contours[0]
    x, y, w, h = cv2.boundingRect(cnt)
    crop = img[y:y+h, x:x+w]
    cv2.imwrite(im_path, crop)

    tex_bounds = TextureBounds(
        min_lat=min_lat_p,
        min_lon=min_lon_p,
        max_lat=max_lat_p,
        max_lon=max_lon_p,
        min_x=min_x,
        min_y=min_y,
        max_x=max_x,
        max_y=max_y,
    )

    with open(texture_bounds_path, 'wb') as f:
        pickle.dump(tex_bounds, f)

    return [im_path, tex_bounds]
