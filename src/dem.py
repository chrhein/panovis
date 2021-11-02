import cv2
import os
import time
import subprocess

import numpy as np
from data_getters.mountains import get_mountain_data
from debug_tools import p_e, p_i, p_line
from location_handler import plot_to_map, get_mountains_in_sight, get_raster_data
from povs import primary_pov, debug_pov
from im import get_image_shape, custom_imshow
from tools.color_map import create_route_texture, \
    create_color_gradient_image, colors_to_coordinates


def render_dem(panorama_path, mode, mountains):
    start_time = time.time()
    panorama_filename = panorama_path.split('/')[-1].split('.')[0]
    folder = 'exports/%s/' % panorama_filename
    gpx_file = 'data/hikes/%s.gpx' % panorama_filename

    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

    dem_file, all_cordinates, pov_settings = get_mountain_data('data/dem-data.json',
                                                               panorama_filename)
    f = dem_file.lower()
    if not f.endswith('.png') and not f.endswith('.jpg'):
        p_e('please provide a .png file')
        return

    panorama = cv2.imread(panorama_path)
    image_width, image_height = get_image_shape(panorama)
    pov_filename = '/tmp/pov_file.pov'
    render_shape = [image_width, image_height]

    render_shape = [int(image_width / 2), image_height]
    c_lat, c_lon, view_points_l, view_points_r = all_cordinates
    v_lat_l, v_lon_l = view_points_l
    v_lat_r, v_lon_r = view_points_r
    coordinates_l = [c_lat, c_lon, v_lat_l, v_lon_l]
    coordinates_r = [c_lat, c_lon, v_lat_r, v_lon_r]

    coors = {
        'l': coordinates_l,
        'r': coordinates_r
    }

    raster_data = get_raster_data(dem_file, coordinates_l, pov_settings[1])
    if not raster_data:
        return

    pov = [pov_filename, folder, render_shape, pov_settings]
    pov_params = [dem_file, pov, raster_data]

    if mode == 'debug':
        route_texture, texture_bounds = create_route_texture(dem_file, gpx_file, True)
        pov_filename, folder, _, _ = pov
        with open(pov_filename, 'w') as pf:
            pov = debug_pov(dem_file, route_texture, texture_bounds, raster_data[1][3])
            pf.write(pov)
            pf.close()
        out_filename = '%srender-debug.png' % folder
        params = [pov_filename, out_filename, [2400, 2400], 'color']
        execute_pov(params)
    else:
        pov_filename, folder, im_dimensions, pov_settings = pov
        if mode == 1:
            pov_mode = 'depth'
            pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
            out_filename = '%srender-%s.png' % (folder, pov_mode)
            params = [pov_filename, out_filename, im_dimensions, pov_mode]
            with open(pov_filename, 'w') as pf:
                pf.write(pov)
            pf.close()
            execute_pov(params)
        elif mode == 2:
            for key, val in coors.items():
                raster_data = get_raster_data(dem_file, val, pov_settings[1])
                pov_mode = 'height'
                pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                out_filename = '%srender-%s-%s.png' % (folder, pov_mode, key)
                params = [pov_filename, out_filename, im_dimensions, 'color']
                with open(pov_filename, 'w') as pf:
                    pf.write(pov)
                pf.close()
                execute_pov(params)
            img1 = cv2.imread('%srender-%s-%s.png' % (folder, pov_mode, 'l'))
            img2 = cv2.imread('%srender-%s-%s.png' % (folder, pov_mode, 'r'))
            vis = np.concatenate((img1, img2), axis=1)
            custom_imshow(vis, 'Preview')
        elif mode == 3:
            pov_mode = 'texture'
            gpx_exists = os.path.isfile('%s' % gpx_file)
            if gpx_exists:
                route_texture, texture_bounds = create_route_texture(dem_file, gpx_file)
                pov_params[1][3].append(route_texture)
                pov_params[1][3].append(texture_bounds)
                pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                out_filename = '%srender-%s.png' % (folder, pov_mode)
                params = [pov_filename, out_filename, im_dimensions, 'color']
                with open(pov_filename, 'w') as pf:
                    pf.write(pov)
                execute_pov(params)
            else:
                p_e('Could not find corresponding GPX')
                return
        elif mode == 4:
            pov_mode = 'gradient'
            out_filename = '%srender-%s.png' % (folder, pov_mode)
            gradient_render = os.path.isfile('%s' % out_filename)
            gradient_path, _ = create_color_gradient_image()
            if not gradient_render:
                pov_settings.append(gradient_path)
                pov = primary_pov(dem_file, raster_data, pov_settings, pov_mode)
                params = [pov_filename, out_filename, im_dimensions, pov_mode]
                with open(pov_filename, 'w') as pf:
                    pf.write(pov)
                execute_pov(params)
            locs = colors_to_coordinates(gradient_path, folder, dem_file)
            mountains_in_sight = get_mountains_in_sight(locs, mountains)
            plot_filename = '%s%s.html' % (folder, panorama_filename)
            plot_to_map(mountains_in_sight, coordinates_l, plot_filename)
        else:
            return
    stats = [
        'Information about completed task: \n',
        'File:      %s' % panorama_filename,
        'Mode:      %s' % mode,
        'Duration:  %i seconds' % (time.time() - start_time)
        ]
    p_line(stats)


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
