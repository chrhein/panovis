import os
import subprocess
from datetime import datetime

from src.colors import *
from src.debug_tools import *
from src.edge_detection import *
from src.location_handler import *
from src.photo_filtering import *
from src.povs import *

from src.data_getters.raster import get_raster_data

def create_depth_image(a_l, out_params):
    pov_filename, out_width, out_height, out_filename = out_params
    with open(pov_filename, 'w') as pf:
        pf.write(pov_script(*a_l))
        pf.close()
        execute_pov(out_width, out_height, pov_filename, out_filename)

def create_color_image(a_l, out_params):
    pov_filename, out_width, out_height, out_filename = out_params
    with open(pov_filename, 'w') as pf:
        pf.write(color_gradient_map(*a_l, "z"))
        pf.close()
        execute_pov(out_width, out_height, pov_filename, out_filename)

def create_coordinate_gradients(raster_data, out_data):
    a_l, ds_raster, total_distance_n_s, total_distance_e_w, tpx_x, tpx_y, = raster_data
    pov_filename, out_width, out_height, out_filename, date = out_data
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
    original_dem = cv2.imread(a_l[6])
    cv2.imwrite(original_raster_dotted,
                cv2.circle(original_dem, (int(z_index / tpx_y), int(x_index / tpx_x)), 25, (0, 0, 255), -1))

    # clear([out_filename, out_filename_x, out_filename_z, point_file, original_raster_dotted])

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
    out_filename = 'exports/rendered_dem_%s.png' % date
    out_width = 2400
    out_height = 800
    pov_filename = '/tmp/pov_file.pov'

    out_data = [pov_filename, out_width, out_height, out_filename, date]

    coordinates = [lat, lon, view_lat, view_lon]
    raster_data = get_raster_data(dem_file, coordinates)
        
    create_coordinate_gradients(raster_data, out_data)
    
    mode='depth1'
    if mode=='depth':
        create_depth_image(raster_data[0], out_data[:4])
    else:
        create_coordinate_gradients(raster_data, out_data)
    try:
        show_image(out_filename)
    except FileNotFoundError:
        p_e("There is probably an error in the .pov file")
        exit()
    p_i("Finished creating panorama for %s" % in_dem)

def execute_pov(out_width, out_height, pov_filename, out_filename):
    p_i("Generating %s" % out_filename)
    subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                     'Output_File_Type=N Bits_Per_Color=8 +Q4 +UR +A',
                     '+I' + pov_filename, '+O' + out_filename])

def show_image(out_filename):
    im = cv2.imread(out_filename)
    cv2.imshow("Result", im)
    cv2.waitKey(0)

def get_date_time():
    dt = datetime.now()
    return "%02d%02d_%02d%02d%02d" % (dt.date().month, dt.date().day,
                                        dt.time().hour, dt.time().minute, dt.time().second)

def clear(clear_list):
    for item in clear_list:
        os.remove(item)
    # subprocess.call(['rm', '-r', 'src/__pycache__'])
