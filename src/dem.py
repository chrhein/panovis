import cv2
import os
import subprocess
from datetime import datetime
import numpy as np
from feature_matching import feature_matching
from edge_detection import edge_detection
from data_getters.mountains import get_mountain_data, get_mountains
from colors import color_interpolator, get_color_from_image
from data_getters.raster import get_raster_data
from debug_tools import p_e, p_i, p_line
from location_handler import crs_to_wgs84, plot_to_map, get_mountains_in_sight
from povs import color_gradient_pov, primary_pov, debug_pov
from tools.color_map import create_route_texture, rgb_to_hex, \
    create_color_gradient_image, load_pickle, colors_to_coordinates


def render_dem(pano, mode):
    filename = pano.split('/')[-1].split('.')[0]
    mountain_data = get_mountain_data('data/dem-data.json', filename)
    dem_file = mountain_data[0]
    coordinates = mountain_data[1]
    pov_settings = mountain_data[2]

    f = dem_file.lower()
    if not f.endswith('.png') and not f.endswith('.jpg'):
        p_e('please provide a .png file')
        exit()

    img = cv2.imread(pano)
    im_height, im_width, _ = img.shape
    new_width = 2800
    new_height = int(new_width * im_height / im_width)
    out_width, out_height = new_width, new_height

    filename = pano.split('/')[-1].split('.')[0]
    folder = 'exports/%s/' % filename
    gpx_file = 'data/hikes/%s.gpx' % filename

    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

    pov_filename = '/tmp/pov_file.pov'
    im_dimensions = [out_width, out_height]
    raster_data = get_raster_data(dem_file, coordinates, pov_settings[1])
    if not raster_data:
        return
    pov = [pov_filename, folder, im_dimensions, pov_settings]
    pov_params = [dem_file, pov, raster_data]

    if mode == 'debug':
        route_texture, texture_bounds = create_route_texture(dem_file, gpx_file, True)
        debug_texture(dem_file, route_texture, texture_bounds, pov, raster_data[1][3])
    elif mode == 1:
        cv2.imwrite(('%s%s.png' % (folder, filename)), cv2.resize(img, [new_width, new_height]))
        create_height_image(*pov_params)
        create_depth_image(*pov_params)
        edge_detection('%s%s.png' % (folder, filename), 'HED',
                       folder, new_width)
        edge_detection('%srender-depth.png' % folder, 'Canny',
                       folder, new_width)
        feature_matching('%sedge-detected-canny.png' % folder,
                         '%sedge-detected-hed.png' % folder, folder,
                         '%s%s.png' % (folder, filename),
                         '%srender-height.png' % folder)
        cv2.destroyAllWindows()
    elif mode == 2:
        create_depth_image(*pov_params)
    elif mode == 3:
        create_height_image(*pov_params)
    elif mode == 4:
        create_coordinate_gradients(*pov_params)
    elif mode == 5:
        show_mountains_in_sight(dem_file, coordinates, folder, filename)
    elif mode == 8:
        route_texture, texture_bounds = create_route_texture(dem_file, gpx_file)
        if route_texture:
            pov_params[1][3].append(route_texture)
            pov_params[1][3].append(texture_bounds)
            create_texture_image(*pov_params)
        else:
            p_e('Could not find corresponding GPX')


def show_mountains_in_sight(dem_file, coordinates, folder, filename):
    gradient_path, _ = create_color_gradient_image()
    mountains = get_mountains('data/mountains/')  # TODO use min and max height from this set
    locs = colors_to_coordinates(gradient_path, folder, dem_file)
    mountains_in_sight = get_mountains_in_sight(locs, mountains)
    plot_filename = '%s%s.html' % (folder, filename)
    plot_to_map(mountains_in_sight, coordinates, plot_filename)


def create_depth_image(dem_file, pov, raster_data):
    # generating pov-ray render using depth mapping
    pov_filename, folder, im_dimensions, pov_settings = pov
    with open(pov_filename, 'w') as pf:
        pov = primary_pov(dem_file, raster_data, pov_settings, 'depth')
        pf.write(pov)
        pf.close()
    out_filename = '%srender-depth.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'depth']
    execute_pov(params)


def create_texture_image(dem_file, pov, raster_data):
    # generating pov-ray render with image texture map
    pov_filename, folder, im_dimensions, pov_settings = pov
    with open(pov_filename, 'w') as pf:
        pov = primary_pov(dem_file, raster_data, pov_settings, 'texture')
        pf.write(pov)
        pf.close()
    out_filename = '%srender-texture.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'color']
    execute_pov(params)


def create_height_image(dem_file, pov, raster_data):
    pov_filename, folder, im_dimensions, pov_settings = pov
    with open(pov_filename, 'w') as pf:
        pov = primary_pov(dem_file, raster_data, pov_settings, 'height')
        pf.write(pov)
        pf.close()
    out_filename = '%srender-height.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'color']
    execute_pov(params)


def create_coordinate_gradients(dem_file, pov, raster_data):
    pov_filename, folder, im_dimensions, pov_settings = pov
    gradient_path, _ = create_color_gradient_image()
    pov_settings.append(gradient_path)

    with open(pov_filename, 'w') as pf:
        pf.write(primary_pov(dem_file, raster_data, pov_settings, 'gradient'))
        pf.close()
    out_filename = '%srender-gradient.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'gradient']
    execute_pov(params)


def execute_pov(params):
    pov_filename, out_filename, dimensions, mode = params
    out_width, out_height = dimensions
    p_i('Generating %s' % out_filename)
    if mode == 'color' or mode == 'gradient':
        subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                         'Output_File_Type=N Bits_Per_Color=16 +Q8 +UR +A',
                         '-GA',
                         '+I' + pov_filename, '+O' + out_filename])
    else:
        subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                         'Output_File_Type=N Bits_Per_Color=16 Display=off',
                         '-GA',
                         'Antialias=off Quality=0 File_Gamma=1.0',
                         '+I' + pov_filename, '+O' + out_filename])


def show_image(out_filename):
    im = cv2.imread(out_filename)
    cv2.imshow('Result', im)
    cv2.waitKey(0)


def visualize_point(folder, image, width, height, m_factor):
    # highlight sample area on original pov-ray render
    point_file = '%s/render_sample_point.png' % (folder)
    cv2.imwrite(point_file, cv2.circle(image,
                                       (int(width * 0.5),
                                        int(height * m_factor)),
                12, (0, 0, 255), -1))


def visualize_point_on_dem(folder, dem_file, x_index,
                           z_index, resolution):
    # highlight sample area on original DEM being used
    original_raster_dotted = '%s/original_dem_sample_point.png' % (folder)
    original_dem = cv2.imread(dem_file)
    cv2.imwrite(original_raster_dotted, cv2.circle(original_dem,
                                                   (int(z_index / resolution),
                                                    int(x_index / resolution)),
                25, (0, 0, 255), -1))


def get_date_time():
    dt = datetime.now()
    return '%02d%02d_%02d%02d%02d' % (dt.date().month, dt.date().day,
                                      dt.time().hour, dt.time().minute,
                                      dt.time().second)


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    subprocess.call(['rm', '-r', 'src/__pycache__'])
    subprocess.call(['rm', '-r', 'src/data_getters/__pycache__'])


def debug_texture(dem_file, texture, bounds, pov, mh):
    # generating pov-ray render with image texture map
    pov_filename, folder, _, _ = pov
    with open(pov_filename, 'w') as pf:
        pov = debug_pov(dem_file, texture, bounds, mh)
        pf.write(pov)
        pf.close()
    out_filename = '%srender-debug.png' % folder
    params = [pov_filename, out_filename, [2400, 2400], 'color']
    execute_pov(params)
