import os
import subprocess
from datetime import datetime

from src.colors import *
from src.debug_tools import *
from src.edge_detection import *
from src.location_handler import *
from src.photo_filtering import *
from src.povs import *


def file_handler(in_dem, lat, lon, view_lat, view_lon):
    render_dem(in_dem, lat, lon, view_lat, view_lon)


def render_dem(in_dem, lat, lon, view_lat, view_lon):
    debug_mode = False
    dem_file = 'exports/tmp_geotiff.png'
    date = 1

    # dem_data_debugger(in_dem, lat, lon, view_lat, view_lon)

    if in_dem.lower().endswith('.dem') or in_dem.lower().endswith('.tif'):
        subprocess.call(['gdal_translate', '-ot', 'UInt16',
                         '-of', 'PNG', '%s' % in_dem, '%s' % dem_file])
    elif in_dem.lower().endswith('.png') or in_dem.lower().endswith('.jpg'):
        dem_file = in_dem
        dt = datetime.now()
        date = "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day,
                                          dt.time().hour, dt.time().minute, dt.time().second)
    else:
        p_e('please provide .dem, .tif or .png')
        exit()

    ds_raster = rasterio.open(dem_file)
    print(ds_raster.bounds)
    tpx = ds_raster.transform
    tpx_x, tpx_y = tpx[0], -tpx[4]
    x, y = ds_raster.xy(10041, 10041)
    print(x - 5, y + 5)
    crs = int(ds_raster.crs.to_authority()[1])
    lat_lon = convert_coordinates(ds_raster, crs, lat, lon)
    view_lat_lon = convert_coordinates(ds_raster, crs, view_lat, view_lon)
    raster_left, raster_bottom, raster_right, raster_top = ds_raster.bounds
    p_line([raster_left, raster_right, raster_top, raster_bottom])
    print(ds_raster)
    bounds = crs_to_wgs84(ds_raster, raster_left, raster_bottom), \
             crs_to_wgs84(ds_raster, raster_right, raster_top)
    lb_lat = bounds[0][0][0]
    lb_lon = bounds[0][1][0]
    ub_lat = bounds[1][0][0]
    yb_lon = bounds[1][1][0]
    p_i("Lower left coordinates:  (%f, %f)" % (lb_lat, lb_lon))
    p_i("Upper right coordinates: (%f, %f)" % (ub_lat, yb_lon))

    total_distance_e_w = abs(raster_left) + abs(raster_right)
    total_distance_n_s = abs(raster_left) + abs(raster_right)
    print(total_distance_n_s)

    out_filename = 'exports/rendered_dem_%s.png' % date
    out_width = 2400
    out_height = 800

    loc_view = get_location(lat_lon[0], lat_lon[1], lat_lon[2], view_lat_lon[0], view_lat_lon[1], view_lat_lon[2])
    location, view = loc_view[0], loc_view[1]
    location_x, location_y, location_height = location[0], location[1], location[2]
    view_x, view_y, view_height = view[0], view[1], view[2]

    try:
        # mode_selection = int(input('Select mode: ')
        mode_selection = 0
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
        color_z, m_factor = get_color_from_image(out_filename_z)
        color_x = get_color_from_image(out_filename_x)[0]
        p_i("r: %f g: %f b: %f" % (color_z[0], color_z[1], color_z[2]))
        p_i(color_z)
        p_line()
        z_index = get_color_index_in_image(color_x, [0, 0, 0], [255, 0, 0], int(total_distance_n_s))
        p_line()
        x_index = get_color_index_in_image(color_z, [255, 0, 0], [0, 0, 0], int(total_distance_e_w))
        p_line()
        p_line(["z-index: %i" % z_index, "x-index: %i" % x_index])
        point_file = 'exports/rendered_dem_%s_point.png' % date
        cv2.imwrite(point_file,
                    cv2.circle(image, (int(width * 0.5), int(height * m_factor)), 18, (0, 0, 255), -1))
        # w, h = get_dataset_bounds(dem_file)

        x, y = ds_raster.xy(x_index / tpx_x, z_index / tpx_y)
        x -= tpx_x / 2
        y += tpx_y / 2
        print(crs_to_wgs84(ds_raster, x, y))

        original_raster_dotted = 'exports/original_dem%s_point.png' % date
        original_dem = cv2.imread(dem_file)
        cv2.imwrite(original_raster_dotted,
                    cv2.circle(original_dem, (int(z_index / tpx_y), int(x_index / tpx_x)), 25, (0, 0, 255), -1))

        # clear([out_filename, out_filename_x, out_filename_z, point_file, original_raster_dotted])

        exit()
    try:
        im = cv2.imread(out_filename)
        edges = edge_detection(im, True, 3)
        cv2.imwrite('canny.png', edges)
        p_i('Created image using Canny Edge Detection')
    except FileNotFoundError:
        p_e("There is probably an error in the .pov file")
        exit()
    # clear([out_filename, out_filename_x, out_filename_z, point_file])
    p_i("Finished creating panorama for %s" % in_dem)


def execute_pov(out_width, out_height, pov_filename, out_filename):
    p_i("Generating %s" % out_filename)
    subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                     'Output_File_Type=N Bits_Per_Color=8 +Q4 +UR +A',
                     '+I' + pov_filename, '+O' + out_filename])


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    # subprocess.call(['rm', '-r', 'src/__pycache__'])
