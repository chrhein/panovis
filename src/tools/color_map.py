import os
import cv2
import numpy as np
import pickle
import rasterio
import subprocess
from osgeo import gdal
from data_getters.mountains import read_hike_gpx
from location_handler import convert_single_coordinate_pair, cor_to_crs, crs_to_cor
from tools.types import TextureBounds
from tools.debug import p_i


# stolen from
# https://www.cocyer.com/python-pillow-generate-gradient-image-with-numpy/


def get_gradient_3d(upper_left_color, lower_right_color, is_horizontal_list):
    height, width = 2 ** 8, 2 ** 8  # number of colors
    result = np.zeros((height, width, len(upper_left_color)), dtype=np.float)

    for i, (start, stop, is_horizontal) in enumerate(
        zip(upper_left_color, lower_right_color, is_horizontal_list)
    ):
        result[:, :, i] = (
            np.tile(np.linspace(start, stop, width), (height, 1))
            if is_horizontal
            else np.tile(np.linspace(start, stop, height), (width, 1)).T
        )
    return result


def create_color_gradient_image():
    gradient_path = f"data/color_gradient.png"
    upper_left_color = (0, 0, 192)
    lower_right_color = (255, 255, 64)
    gradient = np.true_divide(
        get_gradient_3d(upper_left_color, lower_right_color, (True, False, False)),
        255,
    )
    img = cv2.cvtColor(np.uint8(gradient * 255), cv2.COLOR_BGR2RGB)
    cv2.imwrite(gradient_path, img)
    return gradient_path, gradient


def load_pickle(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def create_route_texture(dem_file, gpx_path, debugging=False):
    filename = gpx_path.split("/")[-1].split(".")[0]
    folder = "exports/%s/texture" % filename
    if debugging:
        im_path = "%s/%s-texture-debug.png" % (folder, filename)
    else:
        im_path = "%s/%s-texture.png" % (folder, filename)
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
    texture_bounds_path = "%s/%s-texture-bounds.pkl" % (folder, filename)
    texture_exist = os.path.isfile("%s" % im_path)
    bounds_exist = os.path.isfile("%s" % texture_bounds_path)
    if texture_exist and bounds_exist:
        with open(texture_bounds_path, "rb") as f:
            tex_bounds = pickle.load(f)
        return [im_path, tex_bounds]

    p_i(f"Creating route texture for {filename}")

    mns, minimums, maximums = read_hike_gpx(gpx_path)
    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])
    lower_left = cor_to_crs(crs, minimums[0].latitude, minimums[1].longitude)
    upper_right = cor_to_crs(crs, maximums[0].latitude, maximums[1].longitude)

    bbox = (
        lower_left.GetX(),
        upper_right.GetY(),
        upper_right.GetX(),
        lower_left.GetY(),
    )

    gdal.Translate(
        f"{folder}/{filename}-output_crop_raster.tif", dem_file, projWin=bbox
    )

    im = cv2.imread(f"{folder}/{filename}-output_crop_raster.tif")
    h, w, _ = im.shape
    rs = 1
    if debugging:
        rs = 20

    multiplier = 100

    h = h * multiplier
    w = w * multiplier
    if not mns:
        return ["", ""]
    img = np.ones([h, w, 4], dtype=np.uint8)
    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])
    b = ds_raster.bounds
    bounds = [b.left, b.bottom, b.right, b.top]
    locs = [
        convert_single_coordinate_pair(bounds, crs, i.latitude, i.longitude)
        for i in mns
    ]
    prev_lat = abs(int(((100.0 * locs[0][0]) / 100) * w))
    prev_lon = h - abs(int(100.0 - ((100.0 * locs[0][1]) / 100.0) * h))
    for i in locs:
        lat, lon = i
        x = h - abs(int(100.0 - ((100.0 * lon) / 100.0) * h))
        y = abs(int(((100.0 * lat) / 100.0) * w))
        cv2.line(img, (prev_lat, prev_lon), (y, x), (0, 0, 255, 255), 3 * rs)
        prev_lat, prev_lon = y, x
    min_lat_p = minimums[0]
    min_lon_p = minimums[1]
    max_lat_p = maximums[0]
    max_lon_p = maximums[1]
    min_x = convert_single_coordinate_pair(
        bounds, crs, min_lat_p.latitude, min_lat_p.longitude
    )
    min_y = convert_single_coordinate_pair(
        bounds, crs, min_lon_p.latitude, min_lon_p.longitude
    )
    max_x = convert_single_coordinate_pair(
        bounds, crs, max_lat_p.latitude, max_lat_p.longitude
    )
    max_y = convert_single_coordinate_pair(
        bounds, crs, max_lon_p.latitude, max_lon_p.longitude
    )
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnt = contours[0]
    x, y, w, h = cv2.boundingRect(cnt)
    crop = img[y : y + h, x : x + w]
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

    p_i(f"Route texture complete")

    with open(texture_bounds_path, "wb") as f:
        pickle.dump(tex_bounds, f)

    subprocess.call(["rm", "-r", f"{folder}/{filename}-output_crop_raster.tif"])

    return [im_path, tex_bounds]


def colors_to_coordinates(ds_name, gradient_path, folder, dem_file):
    render_with_gradient = f"{ds_name}-render-gradient.png"
    p_i(f"Finding all visible coordinates in {render_with_gradient}")
    render_path = f"{folder}{render_with_gradient}"
    image = cv2.cvtColor(cv2.imread(render_path), cv2.COLOR_BGR2RGB)
    p_i("Computing list of unique colors")
    unique_colors = np.unique(image.reshape(-1, image.shape[2]), axis=0)[2:]

    p_i("Getting pixel coordinates for colors in render")
    g = cv2.cvtColor(cv2.imread(gradient_path), cv2.COLOR_BGR2RGB)
    color_coordinates = [np.where(np.all(g == i, axis=-1)) for i in unique_colors]
    color_coordinates = [(i[0][0], i[1][0]) for i in color_coordinates if len(i[0]) > 0]

    latlon_color_coordinates = []
    ds_raster = rasterio.open(dem_file)
    ds_raster_height_band = ds_raster.read(1)
    crs = int(ds_raster.crs.to_authority()[1])

    for x, y in color_coordinates:
        s_x, s_y = round(x * (3000 / 256)), round(y * (3000 / 256))
        px, py = ds_raster.xy(s_x, s_y)
        height = ds_raster_height_band[s_x, s_y]
        latlon_color_coordinates.append(crs_to_cor(crs, px, py, height))
    return latlon_color_coordinates


def rgb_to_hex(color, bgr=False):
    r, g, b = color
    color_space = (b, g, r) if bgr else (r, g, b)
    return "%02X%02X%02X" % (color_space)
