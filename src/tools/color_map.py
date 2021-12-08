import os
import cv2
import numpy as np
import pickle
import rasterio
from osgeo import gdal
from data_getters.mountains import read_hike_gpx
from location_handler import convert_single_coordinate_pair, cor_to_crs, crs_to_cor
from image_manipulations import resizer
from tools.types import TextureBounds
from tools.debug import p_i


# stolen from
# https://www.cocyer.com/python-pillow-generate-gradient-image-with-numpy/


def get_gradient_2d(start, stop, width, height, is_horizontal):
    if is_horizontal:
        return np.tile(np.linspace(start, stop, width), (height, 1))
    else:
        return np.tile(np.linspace(start, stop, height), (width, 1)).T


def get_gradient_3d(
    width, height, upper_left_color, lower_right_color, is_horizontal_list
):
    result = np.zeros((height, width, len(upper_left_color)), dtype=np.float)

    for i, (start, stop, is_horizontal) in enumerate(
        zip(upper_left_color, lower_right_color, is_horizontal_list)
    ):
        result[:, :, i] = get_gradient_2d(start, stop, width, height, is_horizontal)
    return result


def create_color_gradient_image():
    gradient_path = "data/color_gradient.png"
    pickle_path = "data/color_gradient.pkl"
    gradient_exist = os.path.isfile("%s" % gradient_path)
    pickle_exist = os.path.isfile("%s" % pickle_path)
    if not (gradient_exist and pickle_exist):
        dem = "./data/bergen.png"
        im = cv2.imread(dem)
        h, w, _ = im.shape
        upper_left_color = (0, 0, 192)
        lower_right_color = (255, 255, 64)
        gradient = np.true_divide(
            get_gradient_3d(
                w, h, upper_left_color, lower_right_color, (True, False, False)
            ),
            255,
        )
        img = cv2.cvtColor(np.uint8(gradient * 255), cv2.COLOR_BGR2RGB)
        with open(pickle_path, "wb") as f:
            pickle.dump(gradient, f)
        cv2.imwrite(gradient_path, img)
    return [gradient_path, pickle_path]


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

    print(bbox)

    gdal.Translate(
        f"{folder}/{filename}-output_crop_raster.tif", dem_file, projWin=bbox
    )

    im = cv2.imread(f"{folder}/{filename}-output_crop_raster.tif")
    h, w, _ = im.shape
    rs = 1
    if debugging:
        rs = 20

    multiplier = 250

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

    print("ferdig med tekstur")

    with open(texture_bounds_path, "wb") as f:
        pickle.dump(tex_bounds, f)

    return [im_path, tex_bounds]


def colors_to_coordinates(gradient_path, folder, dem_file, min_ele=50, max_ele=10000):
    render_path = "%srender-gradient.png" % folder
    coordinates_seen_in_render_path = "%s/coordinates/coordinates.pkl" % folder
    pickle_exists = os.path.isfile("%s" % coordinates_seen_in_render_path)
    gradient = cv2.cvtColor(cv2.imread(gradient_path), cv2.COLOR_BGR2RGB)
    if not pickle_exists:
        image = cv2.cvtColor(cv2.imread(render_path), cv2.COLOR_BGR2RGB)
        image = resizer(image, im_width=200)
        unique_colors = np.unique(image.reshape(-1, image.shape[2]), axis=0)[2:]
        l_ = len(unique_colors)

        color_coordinates = dict()
        div = 1
        for i in range(0, l_, div):
            color = unique_colors[i]
            p_i("%i/%i" % (int((i + 1) / div), int(l_ / div)))
            indices = np.where(np.all(gradient == color, axis=2))
            if len(indices[0]) > 0:
                coordinates = zip(indices[0], indices[1])
                unique_coordinates = list(set(list(coordinates)))
                color_coordinates[rgb_to_hex(color)] = unique_coordinates
        try:
            os.mkdir("%s/coordinates" % folder)
        except FileExistsError:
            pass
        with open(coordinates_seen_in_render_path, "wb") as f:
            pickle.dump(color_coordinates, f)
    else:
        color_coordinates = load_pickle(coordinates_seen_in_render_path)
    latlon_color_coordinates = []
    ds_raster = rasterio.open(dem_file)
    h = ds_raster.read(1)
    crs = int(ds_raster.crs.to_authority()[1])
    use_all_coordinates = False
    for coordinates in color_coordinates.values():
        if use_all_coordinates:
            for coordinate in coordinates:
                x, y = coordinate
                px, py = ds_raster.xy(x, y)
                height = h[x][y]
                latlon = crs_to_cor(crs, px, py, height)
                latlon_color_coordinates.append(
                    latlon
                ) if height >= min_ele and height <= max_ele else None
        else:
            x, y = coordinates[len(coordinates) // 2]
            px, py = ds_raster.xy(x, y)
            height = h[x][y]
            latlon = crs_to_cor(crs, px, py, height)
            latlon_color_coordinates.append(
                latlon
            ) if height >= min_ele and height <= max_ele else None

    return latlon_color_coordinates


def rgb_to_hex(color, bgr=False):
    r, g, b = color
    color_space = (b, g, r) if bgr else (r, g, b)
    return "%02X%02X%02X" % (color_space)
