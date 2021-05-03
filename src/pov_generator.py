import os
import subprocess
from datetime import datetime

import cv2
import numpy as np
import rasterio

from src.debug_tools import p_i, p_e
from src.edge_detection import edge_detection
from src.location_handler import convert_coordinates, get_location
from src.povs import pov_script, color_pov, color_gradient_map


def file_handler(in_dem, lat, lon, view_lat, view_lon):
    render_dem(in_dem, lat, lon, view_lat, view_lon)


def render_dem(in_dem, lat, lon, view_lat, view_lon):
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

    out_filename = 'exports/rendered_dem_%s.png' % date
    out_width = 2400
    out_height = 800

    loc_view = get_location(lat_lon[0], lat_lon[1], lat_lon[2], view_lat_lon[0], view_lat_lon[1], view_lat_lon[2])
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]

    try:
        mode_selection = int(input('Select mode: '))
    except ValueError:
        p_e("No integer provided, default mode selected")
        mode_selection = 0
        p_i("Continuing...")
    a_l = [location_x, location_height, location_y,
           view_x, view_height, view_y,
           dem_file]

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
        p_i(get_image_rgb_list(out_filename_x))
        p_i(get_image_rgb_list(out_filename_z))
        image = cv2.imread(out_filename)
        height, width, _ = image.shape
        m_factor = 0.0
        while True:
            color = get_image_rgb_list(out_filename_x, m_factor)
            if color[0] != 0 or color[2] != 0 or color[2] != 0:
                break
            if m_factor >= 1:
                m_factor = 0.5
                break
            m_factor += 0.01
        p_i("m_factor used: %i" % m_factor)
        p_i("r: %i g: %i b: %i" %(color[0], color[1], color[2]))
        cv2.imwrite('exports/rendered_dem_%s_point.png' % date,
                    cv2.circle(image, (int(width * 0.5), int(height * m_factor)), 18, (0, 0, 255), -1))
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


def get_image_rgb_list(image_path, m_factor=0.55):
    image = cv2.imread(image_path, cv2.IMREAD_COLOR)
    height, width, _ = image.shape
    color = image[int(height * m_factor), int(width * 0.5)]
    color = np.array_split(color, 3)
    b, g, r = color
    return r[0], g[0], b[0]


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    subprocess.call(['rm', '-r', 'src/__pycache__'])
