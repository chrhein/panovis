from cv2 import cv2
import os
import subprocess
from datetime import datetime
from src.colors import get_color_from_image, get_color_index_in_image
from src.data_getters.raster import get_raster_data
from src.debug_tools import p_e, p_i, p_line
from src.location_handler import crs_to_wgs84
from src.povs import color_gradient_map, pov_script


def create_depth_image(a_l, out_params):
    with open(out_params[2], 'w') as pf:
        pf.write(pov_script(*a_l))
        pf.close()
    execute_pov(*out_params)


def create_color_image(a_l, out_params):
    with open(out_params[2], 'w') as pf:
        pf.write(color_gradient_map(*a_l, "z"))
        pf.close()
    execute_pov(*out_params)


def create_coordinate_gradients(raster_data, out_data):
    a_l, ds_raster, total_distance_n_s, total_distance_e_w, tpx_x, tpx_y, = raster_data

    # generating two gradient colored pov-ray renders
    out_filename_x = '/tmp/rendered_dem_%s_x.png' % out_data[4]
    with open(out_data[2], 'w') as pf:
        pf.write(color_gradient_map(*a_l, "x"))
        pf.close()
    execute_pov(*out_data[:3], out_filename_x)

    out_filename_z = '/tmp/rendered_dem_%s_z.png' % out_data[4]
    with open(out_data[2], 'w') as pf:
        pf.write(color_gradient_map(*a_l, "z"))
        pf.close()
    execute_pov(*out_data[:3], out_filename_z)

    # using the colors of each photo to pinpoint where we are looking at
    color_z = get_color_from_image(out_filename_z)[0]
    color_x = get_color_from_image(out_filename_x)[0]
    z_index = get_color_index_in_image(color_x, [0, 0, 0], [255, 0, 0], int(total_distance_n_s))
    x_index = get_color_index_in_image(color_z, [255, 0, 0], [0, 0, 0], int(total_distance_e_w))


    # printing estimated coordinates for the centermost point of the generated pov-ray render
    x, y = ds_raster.xy(x_index / tpx_x, z_index / tpx_y)
    x -= tpx_x / 2
    y += tpx_y / 2
    latitude, longitude = crs_to_wgs84(ds_raster, x, y)
    p_line(["Latitude: %f" % float(str(latitude).strip("[]")), "Longitude: %f" % float(str(longitude).strip("[]"))])
    

def render_dem(in_dem, lat, lon, view_lat, view_lon):
    if in_dem.lower().endswith('.dem') or in_dem.lower().endswith('.tif'):
        dem_file = 'exports/tmp_geotiff.png'
        subprocess.call(['gdal_translate', '-ot', 'UInt16',
                         '-of', 'PNG', '%s' % in_dem, '%s' % dem_file])
    elif in_dem.lower().endswith('.png') or in_dem.lower().endswith('.jpg'):
        dem_file = in_dem
    else:
        p_e('please provide .dem, .tif or .png')
        exit()

    date = get_date_time()
    out_filename = '/tmp/rendered_dem_%s.png' % date
    out_width = 2400
    out_height = 800
    pov_filename = '/tmp/pov_file.pov'

    out_data = [out_width, out_height, pov_filename, out_filename, date]

    coordinates = [lat, lon, view_lat, view_lon]
    raster_data = get_raster_data(dem_file, coordinates)

    mode='depth'
    if mode=='depth':
        create_depth_image(raster_data[0], out_data[:4])
        try:
            show_image(out_filename)
        except FileNotFoundError:
            p_e("There is probably an error in the .pov file")
            exit()
        p_i("Finished creating panorama for %s" % in_dem)
    else:
        create_coordinate_gradients(raster_data, out_data)
    

def execute_pov(out_width, out_height, pov_filename, out_filename):
    p_i("Generating %s" % out_filename)
    subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                     'Output_File_Type=N Bits_Per_Color=8 +Q4 +UR +A',
                     '+I' + pov_filename, '+O' + out_filename])


def show_image(out_filename):
    im = cv2.imread(out_filename)
    cv2.imshow("Result", im)
    cv2.waitKey(0)


def visualize_point(image, width, height, m_factor, date):
    point_file = 'exports/rendered_dem_%s_point.png' % date
    cv2.imwrite(point_file,
                cv2.circle(image, (int(width * 0.5), int(height * m_factor)), 18, (0, 0, 255), -1))


def visualize_point_on_dem(a_l, x_index, z_index, tpx_x, tpx_y, date):
    original_raster_dotted = 'exports/original_dem%s_point.png' % date
    original_dem = cv2.imread(a_l[6])
    cv2.imwrite(original_raster_dotted,
                cv2.circle(original_dem, (int(z_index / tpx_y), int(x_index / tpx_x)), 25, (0, 0, 255), -1))


def get_date_time():
    dt = datetime.now()
    return "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day,
                                        dt.time().hour, dt.time().minute, dt.time().second)


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
