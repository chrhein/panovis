import cv2
import numpy as np
import rasterio
from src.location_handler import crs_to_wgs84
from src.image_manipulations import resizer
from src.colors import color_interpolator, get_color_from_image, get_color_index_in_image, get_unique_colors_in_image
from src.debug_tools import p_e, p_i, p_in, p_line
from src.feature_matching import feature_matching
from src.edge_detection import edge_detection
from src.dem import render_dem
from tkinter.filedialog import askopenfile, askopenfilenames
import tkinter as tk
import os
import pandas as pd
from shapely.geometry import Point
import geopandas as gpd
from geopandas import GeoDataFrame
import plotly.express as px
import pandas as pd


def get_input():
    p_i("Select one of these modes to continue:")
    information_text = [
        "1: autopilot",
        "2: create 3d depth pov-ray render from DEM",
        "3: create a 3d height pov-ray render from DEM",
        "4: render-to-coordinates",
        "5: edge detection in given image",
        "6: feature matching given two images",
        "0: exit program"
    ]
    p_line(information_text)

    while True:
        try:
            mode = int(p_in("Select mode: "))
        except ValueError:
            p_e('No valid mode given.')
            continue
        else:
            if mode == 0:
                exit()
            if mode < 1 or mode > len(information_text):
                p_e('No valid mode given.')
                continue
            return mode


def edge_detection_type():
    p_i("Select one of these algorithms to continue:")
    information_text = [
        "1: Canny",
        "2: Holistically-Nested (HED)",
        "3: Horizon Highlighting",
        "0: exit program"
    ]
    p_line(information_text)

    while True:
        try:
            mode = int(p_in("Select algorithm: "))
        except ValueError:
            p_e('No valid algorithm given.')
            continue
        else:
            if mode == 0:
                exit()
            if mode < 1 or mode > len(information_text):
                p_e('No valid algorithm given.')
                continue
            return mode


def file_chooser(title, multiple=False):
    # Set environment variable
    os.environ['TK_SILENCE_DEPRECATION'] = "1"
    root = tk.Tk()
    root.withdraw()
    p_i("Opening File Explorer")
    if multiple:
        files = askopenfilenames(title=title,
                                 filetypes=[('PNGs', '*.png'),
                                            ('JPEGs', '*.jpeg'),
                                            ('JPGs', '*.jpg')])
    else:
        filename = askopenfile(title=title,
                               mode='r',
                               filetypes=[('PNGs', '*.png'),
                                          ('JPEGs', '*.jpeg'),
                                          ('JPGs', '*.jpg')])
    try:
        if multiple:
            p_i("%s was selected" % [i.split('/')[-1] for i in files])
            return files
        else:
            p_i("%s was selected" % filename.name.split('/')[-1])
            return filename.name
    except AttributeError:
        p_i("Exiting...")
        exit()


def handle_im(img):
    img = cv2.imread(img)
    d = resizer(img, im_width=2800)
    return get_unique_colors_in_image(d)


class Location:
    # data members of class
    longitude = 0
    latitude = 0

    def __init__(self, latitude, longitude):
        self.latitude = latitude
        self.longitude = longitude


def get_loc(x_color, y_color, x_colors, y_colors, ds_raster):
    x = get_color_index_in_image(x_color, x_colors)
    y = get_color_index_in_image(y_color, y_colors)
    x, y = ds_raster.xy(x*0.10, y*0.10)
    latitude, longitude = crs_to_wgs84(ds_raster, x, y)
    return (float(str(latitude).strip('[]')),
            float(str(longitude).strip('[]')))


def coordinate_lookup(im1, im2):
    c_lat = 60.41454411362287
    c_lon = 5.3896563433223585
    l_lat = 60.37781556563401
    l_lon = 5.387034486694265
    ds = rasterio.open('data/hordaland.png')
    h1, w1, _ = im1.shape
    x_int_c = color_interpolator([255, 0, 0], [0, 0, 0], 100410)
    y_int_c = color_interpolator([0, 0, 0], [255, 0, 0], 100410)
    locs = set(get_loc(im2[i, j], im1[i, j], x_int_c, y_int_c, ds)
               for i in range(0, h1, 3)
               for j in range(0, w1, 3)
               if im2[i, j][1] != 255)
    df = pd.DataFrame(locs, columns=['lat', 'lon'])
    fig = px.scatter_geo(df, lat='lat', lon='lon')
    fig.add_scattergeo(lat=[c_lat], lon=[c_lon])
    fig.add_scattergeo(lat=[l_lat], lon=[l_lon])
    fig.update_layout(title='Results', title_x=0.5, geo_scope='europe')
    lat_foc = df['lat'].iloc[0]
    lon_foc = df['lon'].iloc[0]
    fig.update_layout(
            geo=dict(
                projection_scale=125,
                center=dict(lat=lat_foc, lon=lon_foc)
            ))
    fig.show()
    exit()


def colortesting():
    im1 = cv2.imread('exports/panorama1/render-loc_x.png')
    im1 = cv2.cvtColor(im1, cv2.COLOR_BGR2RGB)
    im1 = resizer(im1, im_width=200)
    im2 = cv2.imread('exports/panorama1/render-loc_z.png')
    im2 = cv2.cvtColor(im2, cv2.COLOR_BGR2RGB)
    im2 = resizer(im2, im_width=200)
    coordinate_lookup(im1, im2)
    exit()
    """ x_c = handle_im('exports/panorama1/render-loc_x.png')
    y_c = handle_im('exports/panorama1/render-loc_z.png')

    x_idxs = [get_color_index_in_image(i,
                                       [0, 0, 0],
                                       [255, 0, 0],
                                       int(100410)) for i in x_c]
    y_idxs = [get_color_index_in_image(i,
                                       [0, 0, 0],
                                       [255, 0, 0],
                                       int(100410)) for i in y_c]

    print(x_idxs)
    print(y_idxs) """

    x = [18507, 2363, 22445, 11419, 13782, 7482, 2756, 16144, 6694, 16538, 20870, 12207, 16932, 5906, 21263, 22051, 17326, 5119, 1181, 12994, 14963, 1575, 6300, 21657, 10632, 100410, 1969, 15357, 19688, 11025, 13388, 7088, 4725, 20082, 15751, 0, 9844, 394, 4331, 22838, 20476, 9450, 11813, 5513, 788, 14176, 23232, 18113, 14569, 19294, 3150, 3544, 18901, 10238, 12600, 3938, 7875, 8269, 9057, 8663, 17719]
    y = [18507, 2363, 11419, 13782, 7482, 6694, 16538, 36620, 25595, 34651, 30714, 10632, 11025, 4725, 7088, 33864, 0, 9844, 29926, 29139, 22838, 34258, 27957, 10238, 3938, 8269, 4331, 33470, 27170, 32289, 22445, 16144, 27564, 1575, 21657, 15357, 100410, 26776, 19688, 15751, 13388, 24807, 788, 35045, 18901, 12600, 24020, 7875, 12994, 9057, 35833, 31107, 36226, 12207, 5906, 21263, 5119, 17326, 1181, 6300, 30320, 35439, 31501, 24413, 29532, 9450, 11813, 5513, 14569, 3544, 23626, 32682, 28745, 17719, 8663, 2756, 31895, 37014, 20870, 16932, 25988, 22051, 14963, 1969, 33076, 20082, 25201, 18113, 20476, 14176, 23232, 19294, 3150, 28351, 37408, 26382]

    ds_raster = rasterio.open('data/hordaland.png')

    locs = [ds_raster.xy(x_idx / 10, y_idx / 10) for x_idx in x for y_idx in y]

    latitude, longitude = crs_to_wgs84(ds_raster, locs[0][0], locs[0][1])

    p_i('%.20f, %.20f' % (float(str(latitude).strip('[]')),
                          float(str(longitude).strip('[]'))))

    print(latitude, longitude)

    exit()


if __name__ == '__main__':
    colortesting()

    mode = get_input()

    if 0 < mode < 5:
        panos = file_chooser('Select an image to detect edges on', True)
        for pano in panos:
            render_dem(pano, mode)
        p_i('Autopilot complete.')
    elif mode == 5:
        kind = edge_detection_type()
        image = file_chooser('Select an image to detect edges on')
        if kind == 1:
            edge_detection(image, "Canny")
        elif kind == 2:
            edge_detection(image, "HED")
        elif kind == 3:
            edge_detection(image, "Horizon")
    elif mode == 6:
        image1 = file_chooser('Select render')
        image2 = file_chooser('Select image')
        feature_matching(image1, image2)
