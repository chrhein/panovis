from cv2 import cv2
import os
import subprocess
from datetime import datetime
from src.colors import get_color_from_image, get_color_index_in_image
from src.data_getters.raster import get_raster_data
from src.debug_tools import p_e, p_i, p_line
from src.location_handler import crs_to_wgs84
from src.povs import color_gradient_pov, depth_pov


def render_dem(input_file, coordinates, mode, persistent):
    f = input_file.lower()
    if f.endswith('.dem') or f.endswith('.tif'):
        # convert DEM to GeoTIFF
        dem_file = 'exports/tmp_geotiff.png'
        subprocess.call(['gdal_translate', '-ot', 'UInt16',
                         '-of', 'PNG', '%s' % input_file, '%s' % dem_file])
    elif f.endswith('.png') or f.endswith('.jpg'):
        dem_file = input_file
    else:
        p_e('please provide .dem, .tif or .png')
        exit()

    out_folder = '/tmp/'
    if persistent: out_folder = 'exports/'

    date = get_date_time()
    out_filename = '%srendered_dem_%s.png' % (out_folder, date)
    out_width, out_height = 2400, 800
    pov_filename = '/tmp/pov_file.pov'

    out_data = [out_width, out_height, pov_filename, out_filename, out_folder, date]
    raster_data = get_raster_data(dem_file, coordinates)

    if mode==1:
        create_depth_image(raster_data[0], out_data[:4])
        try:
            show_image(out_filename)
        except FileNotFoundError:
            p_e("There is probably an error in the .pov file")
            exit()
        p_i("Finished creating panorama for %s" % input_file)
    elif mode==2:
        create_coordinate_gradients(raster_data, out_data)
    
    clear([])


def create_depth_image(coordinates_and_dem, out_params):
    # generating pov-ray render using depth mapping
    with open(out_params[2], 'w') as pf:
        pf.write(depth_pov(*coordinates_and_dem))
        pf.close()
    execute_pov(*out_params)


def create_color_image(coordinates_and_dem, out_params):
    # generating gradient colored pov-ray render
    with open(out_params[2], 'w') as pf:
        pf.write(color_gradient_pov(*coordinates_and_dem, "z"))
        pf.close()
    execute_pov(*out_params)


def create_coordinate_gradients(raster_data, out_data):
    coordinates_and_dem, ds_raster, total_distance_n_s, \
        total_distance_e_w, resolution = raster_data
    
    out_width, out_height, pov_filename, out_filename, folder, date = out_data

    # generating two gradient colored pov-ray renders
    out_filename_x = '%srendered_dem_%s_x.png' % (folder, date)
    with open(pov_filename, 'w') as pf:
        pf.write(color_gradient_pov(*coordinates_and_dem, "x"))
        pf.close()
    execute_pov(*out_data[:3], out_filename_x)

    out_filename_z = '%srendered_dem_%s_z.png' % (folder, date)
    with open(pov_filename, 'w') as pf:
        pf.write(color_gradient_pov(*coordinates_and_dem, "z"))
        pf.close()
    execute_pov(*out_data[:3], out_filename_z)

    # using the colors of each photo to pinpoint where we are looking at
    color_z, m_factor = get_color_from_image(out_filename_z)
    color_x = get_color_from_image(out_filename_x)[0]
    z_index = get_color_index_in_image(color_x, \
        [0, 0, 0], [255, 0, 0], int(total_distance_n_s))
    x_index = get_color_index_in_image(color_z, \
        [255, 0, 0], [0, 0, 0], int(total_distance_e_w))


    # printing estimated coordinates for the centermost point of the generated pov-ray render
    x, y = ds_raster.xy(x_index / resolution, z_index / resolution)
    x -= resolution / 2
    y += resolution / 2
    latitude, longitude = crs_to_wgs84(ds_raster, x, y)
    p_line(["Latitude: %f" % float(str(latitude).strip("[]")), \
        "Longitude: %f" % float(str(longitude).strip("[]"))])

    if(folder!="/tmp/"):
        with open(pov_filename, 'w') as pf:
            pf.write(depth_pov(*coordinates_and_dem))
            pf.close()
        execute_pov(*out_data[:3], out_filename)
        image = cv2.imread(out_filename)
        height, width, _ = image.shape
        out_params = [folder, date]
        visualize_point(out_params, image, width, height, m_factor)
        visualize_point_on_dem(out_params, coordinates_and_dem, x_index, z_index, resolution)

    

def execute_pov(out_width, out_height, pov_filename, out_filename):
    p_i("Generating %s" % out_filename)
    # calling subprocess which triggers the pov_filename parameter
    subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                     'Output_File_Type=N Bits_Per_Color=8 +Q4 +UR +A',
                     '+I' + pov_filename, '+O' + out_filename])


def show_image(out_filename):
    im = cv2.imread(out_filename)
    cv2.imshow("Result", im)
    cv2.waitKey(0)


def visualize_point(out_params, image, width, height, m_factor):
    # highlight sample area on original pov-ray render
    folder, date = out_params
    point_file = '%s/rendered_dem_%s_point.png' % (folder, date)
    cv2.imwrite(point_file, cv2.circle(image, \
        (int(width * 0.5), int(height * m_factor)), 18, (0, 0, 255), -1))


def visualize_point_on_dem(out_params, coordinates_and_dem, x_index, z_index, resolution):
    # highlight sample area on original DEM being used
    folder, date = out_params
    original_raster_dotted = '%s/original_dem%s_point.png' % (folder, date)
    original_dem = cv2.imread(coordinates_and_dem[6])
    cv2.imwrite(original_raster_dotted, cv2.circle(original_dem, \
        (int(z_index / resolution), int(x_index / resolution)), 25, (0, 0, 255), -1))


def get_date_time():
    dt = datetime.now()
    return "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day, \
        dt.time().hour, dt.time().minute, dt.time().second)


def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    subprocess.call(['rm', '-r', 'src/__pycache__'])
    subprocess.call(['rm', '-r', 'src/data_getters/__pycache__'])
