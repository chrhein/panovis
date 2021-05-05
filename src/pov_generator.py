import os
import subprocess
from datetime import datetime
from math import sqrt

import cv2
import numpy as np
import rasterio

from src.debug_tools import p_i, p_e, p_line
from src.edge_detection import edge_detection
from src.location_handler import convert_coordinates, get_location
from src.povs import pov_script, color_pov, color_gradient_map


def file_handler(in_dem, lat, lon, view_lat, view_lon):
    render_dem(in_dem, lat, lon, view_lat, view_lon)


def render_dem(in_dem, lat, lon, view_lat, view_lon):
    colors = color_interpolator([0, 0, 0], [255, 0, 0], 100000)
    o_r, o_g, o_b = get_image_rgb_list("exports/rendered_dem_0505_181347_z.png", 0.55, 1)
    p_i("Searching for: %i, %i, %i" % (o_r, o_g, o_b))

    idx = 0
    saved_index = 0
    lowest = 1000
    for col in colors:
        r, g, b = col
        new_low_r = abs(r - o_r)
        if new_low_r < lowest:
            p_i(r)
            lowest = new_low_r
            saved_index = idx
        idx += 1

    p_i(lowest)
    p_i(saved_index)
    p_i("Found nearest color: %i, %i, %i" % (
    round(colors[saved_index][0]), round(colors[saved_index][1]), round(colors[saved_index][2])))
    p_line()
    exit()

    r, g, b = o_r, o_g, o_b
    color_diffs = []
    for color in colors:
        cr, cg, cb = color
        color_diff = sqrt(abs((r - cr) * o_r) ** 2 + abs((g - cg) * o_g) ** 2)
        color_diffs.append((color_diff, color))

    new_color_diffs = sorted(color_diffs)
    index = color_diffs.index(new_color_diffs[0])
    p_i("Found nearest color: %.0f, %.0f, %.0f" % (
    colors[index][0] * 255, colors[index][1] * 255, colors[index][2] * 255))
    p_i("Index: %i" % index)
    exit()
    debug_mode = False
    dem_file = 'exports/tmp_geotiff.png'
    date = 1

    # dem_data_debugger(in_dem, lat, lon, view_lat, view_lon)

    if in_dem.lower().endswith('.dem') or in_dem.lower().endswith('.tif'):
        subprocess.call(['gdal_translate', '-ot', 'UInt16',
                         '-of', 'PNG', '%s' % in_dem, '%s' % dem_file])
    elif in_dem.lower().endswith('.png'):
        dem_file = in_dem
        dt = datetime.now()
        date = "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day,
                                          dt.time().hour, dt.time().minute, dt.time().second)
    else:
        p_e('please provide .dem, .tif or .png')
        exit()

    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])
    lat_lon = convert_coordinates(ds_raster, crs, lat, lon)
    view_lat_lon = convert_coordinates(ds_raster, crs, view_lat, view_lon)

    """
    raster_left, raster_bottom, raster_right, raster_top = ds_raster.bounds
    bounds = crs_to_wgs84(ds_raster, raster_left, raster_bottom), crs_to_wgs84(ds_raster, raster_right, raster_top)
    lb_lat = bounds[0][0][0]
    lb_lon = bounds[0][1][0]
    ub_lat = bounds[1][0][0]
    yb_lon = bounds[1][1][0]
    p_i("Lower left coordinates:  (%f, %f)" % (lb_lat, lb_lon))
    p_i("Upper right coordinates: (%f, %f)" % (ub_lat, yb_lon))

    total_distance_l_r = abs(raster_left) + abs(raster_right)
    p_i(total_distance_l_r)
    total_distance_l_r = abs(raster_top) - abs(raster_bottom)
    p_i(total_distance_l_r)

    view_cors = cor_to_crs(crs, view_lat, view_lon)
    view_x = view_cors.GetX()
    dist_x = abs(raster_bottom) - abs(view_x)

    p_i(dist_x)
    colors = color_interpolator([255, 0, 0], [0, 255, 0], int(total_distance_l_r))
    p_i(colors)
    p_line([[230, 126, 0] in colors])
    """

    out_filename = 'exports/rendered_dem_%s.png' % date
    out_width = 2400
    out_height = 800

    loc_view = get_location(lat_lon[0], lat_lon[1], lat_lon[2], view_lat_lon[0], view_lat_lon[1], view_lat_lon[2])
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]

    try:
        # mode_selection = int(input('Select mode: ')
        mode_selection = 2
    except ValueError:
        p_e("No integer provided, default mode selected")
        mode_selection = 0
        p_i("Continuing...")

    if debug_mode:
        a_l = [0.5, 1.0, -0.1,
               0.5, 0.0, 0.4,
               dem_file]
    else:
        a_l = [location_x, location_height, location_y,
               view_x, view_height, view_y,
               dem_file]
    # debug mode

    pov_filename = '/tmp/pov_file.pov'
    if mode_selection == 0 or mode_selection == 1:
        with open(pov_filename, 'w') as pf:
            if mode_selection == 1:
                p_i("Color mode selected")
                pov = color_pov(a_l[0], a_l[1], a_l[2], a_l[3], a_l[4], a_l[5], a_l[6])
            else:
                p_i("Depth map mode selected")
                pov = pov_script(a_l[0], a_l[1], a_l[2], a_l[3], a_l[4], a_l[5], a_l[6])
            pf.write(pov)
            pf.close()
        execute_pov(out_width, out_height, pov_filename, out_filename)
    else:
        p_i("Multicolor mode selected")
        with open(pov_filename, 'w') as pf:
            pf.write(pov_script(a_l[0], a_l[1], a_l[2], a_l[3], a_l[4], a_l[5], a_l[6]))
            pf.close()
        execute_pov(out_width, out_height, pov_filename, out_filename)
        pov_filename = '/tmp/pov_x.pov'
        out_filename_x = 'exports/rendered_dem_%s_x.png' % date
        with open(pov_filename, 'w') as pf:
            pf.write(color_gradient_map(a_l[0], a_l[1], a_l[2], a_l[3], a_l[4], a_l[5], a_l[6], "x"))
            pf.close()
        execute_pov(out_width, out_height, pov_filename, out_filename_x)
        pov_filename = '/tmp/pov_z.pov'
        out_filename_z = 'exports/rendered_dem_%s_z.png' % date
        with open(pov_filename, 'w') as pf:
            pf.write(color_gradient_map(a_l[0], a_l[1], a_l[2], a_l[3], a_l[4], a_l[5], a_l[6], "z"))
            pf.close()
        execute_pov(out_width, out_height, pov_filename, out_filename_z)
        image = cv2.imread(out_filename)
        height, width, _ = image.shape
        m_factor = 0.0
        while True:
            color = get_image_rgb_list(out_filename_z, m_factor)
            if color[0] != 0.0 or color[1] != 0.0 or color[2] != 0.0:
                break
            if m_factor >= 1.0:
                m_factor = 0.5
                break
            m_factor += 0.01
        p_i("m_factor used: %.2f" % m_factor)
        p_i("r: %f g: %f b: %f" % (color[0], color[1], color[2]))
        p_i(color)
        cv2.imwrite('exports/rendered_dem_%s_point.png' % date,
                    cv2.circle(image, (int(width * 0.5), int(height * m_factor)), 18, (0, 0, 255), -1))
        p_i(color in get_unique_colors_in_image(out_filename_z))
        # w, h = get_dataset_bounds(dem_file)
        exit()
    try:
        im = cv2.imread(out_filename)
        edges = edge_detection(im, True, 3)
        cv2.imwrite('canny.png', edges)
        p_i('Created image using Canny Edge Detection')
    except FileNotFoundError:
        p_e("There is probably an error in the .pov file")
        exit()
    # clear([out_filename])
    p_i("Finished creating panorama for %s" % in_dem)


def execute_pov(out_width, out_height, pov_filename, out_filename):
    p_i("Generating %s" % out_filename)
    subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                     'Output_File_Type=N Bits_Per_Color=8 +Q4 +UR +A',
                     '+I' + pov_filename, '+O' + out_filename])


def get_image_rgb_list(image_path, m_factor=0.55, color_space=1):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    # image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    height, width, _ = image.shape
    color = image[int(height * m_factor), int(width * 0.5)]
    color = np.array_split(color, 3)
    r, g, b = color
    return r[0] / color_space, g[0] / color_space, b[0] / color_space


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    subprocess.call(['rm', '-r', 'src/__pycache__'])


def color_interpolator(from_color, to_color, size):
    color_gradient = []
    for i in range(size + 1):
        r = (to_color[0] - from_color[0]) * i / size + from_color[0]
        g = (to_color[1] - from_color[1]) * i / size + from_color[1]
        b = (to_color[2] - from_color[2]) * i / size + from_color[2]
        color_gradient.append([r, 0, 0])
    return color_gradient


def get_unique_colors_in_image(image):
    image = cv2.imread(image)
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    return set(tuple(v) for m2d in image for v in m2d)
