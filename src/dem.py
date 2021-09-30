import cv2
import os
import subprocess
from datetime import datetime
from src.feature_matching import feature_matching
from src.edge_detection import edge_detection
from src.data_getters.mountains import get_mountain_data
from src.colors import color_interpolator, get_color_from_image, get_color_index_in_image
from src.data_getters.raster import get_raster_data
from src.debug_tools import p_e, p_i, p_line
from src.location_handler import crs_to_wgs84
from src.povs import color_gradient_pov, depth_pov, height_pov


def render_dem(pano, mode):
    mountain_data = get_mountain_data('data/dem-data.json', pano)
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

    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

    cv2.imwrite(('%s%s.png' % (folder, filename)),
                cv2.resize(img, [new_width, new_height]))

    pov_filename = '/tmp/pov_file.pov'
    im_dimensions = [out_width, out_height]
    raster_data = get_raster_data(dem_file, coordinates, pov_settings[1])
    pov = [pov_filename, folder, im_dimensions, pov_settings]
    pov_params = [dem_file, pov, raster_data]

    if mode == 1:
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


def create_depth_image(dem_file, pov, raster_data):
    # generating pov-ray render using depth mapping
    pov_filename, folder, im_dimensions, pov_settings = pov
    with open(pov_filename, 'w') as pf:
        pov = depth_pov(dem_file, raster_data, pov_settings)
        pf.write(pov)
        pf.close()
    out_filename = '%srender-depth.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'depth']
    execute_pov(params)


def create_color_image(coordinates_and_dem, out_params):
    # generating gradient colored pov-ray render
    with open(out_params[2], 'w') as pf:
        pf.write(color_gradient_pov(*coordinates_and_dem, 'z'))
        pf.close()
    execute_pov(*out_params)


def create_height_image(dem_file, pov, raster_data):
    pov_filename, folder, im_dimensions, pov_settings = pov
    with open(pov_filename, 'w') as pf:
        pov = height_pov(dem_file, raster_data, pov_settings)
        pf.write(pov)
        pf.close()
    out_filename = '%srender-height.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'color']
    execute_pov(params)


def create_coordinate_gradients(dem_file, pov, raster_data):
    pov_filename, folder, im_dimensions, pov_settings = pov

    ds_raster = raster_data[1][0]
    total_distance_n_s, total_distance_e_w = raster_data[1][1]
    resolution = raster_data[1][2]

    with open(pov_filename, 'w') as pf:
        pf.write(color_gradient_pov(dem_file, raster_data, pov_settings, 'x'))
        pf.close()
    out_filename_x = '%srender-loc_x.png' % folder
    params = [pov_filename, out_filename_x, im_dimensions, 'loc_x']
    execute_pov(params)

    with open(pov_filename, 'w') as pf:
        pf.write(color_gradient_pov(dem_file, raster_data, pov_settings, 'z'))
        pf.close()
    out_filename_z = '%srender-loc_z.png' % folder
    params = [pov_filename, out_filename_z, im_dimensions, 'loc_z']
    execute_pov(params)

    # using the colors of each photo to pinpoint where we are looking at
    color_z, m_factor = get_color_from_image(out_filename_z)
    color_x = get_color_from_image(out_filename_x)[0]
    x_colors = color_interpolator([0, 0, 0], [255, 0, 0],
                                  int(total_distance_n_s))
    y_colors = color_interpolator([255, 0, 0], [0, 0, 0],
                                  int(total_distance_e_w))
    z_index = get_color_index_in_image(color_x,
                                       x_colors)
    x_index = get_color_index_in_image(color_z,
                                       y_colors)

    x, y = ds_raster.xy(x_index / resolution, z_index / resolution)
    print(x, y)

    x -= resolution / 2
    y += resolution / 2
    latitude, longitude = crs_to_wgs84(ds_raster, x, y)

    with open(pov_filename, 'w') as pf:
        pf.write(depth_pov(dem_file, raster_data, pov_settings))
        pf.close()
    out_filename = '%srender-depth.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'depth']
    execute_pov(params)

    image = cv2.imread(out_filename)
    height, width, _ = image.shape
    visualize_point(folder, image, width, height, m_factor)
    visualize_point_on_dem(folder, dem_file, x_index, z_index, resolution)
    p_line(['Latitude: %.20f' % float(str(latitude).strip('[]')),
            'Longitude: %.20f' % float(str(longitude).strip('[]'))])
    p_i('%.20f, %.20f' % (float(str(latitude).strip('[]')),
                          float(str(longitude).strip('[]'))))


def execute_pov(params):
    pov_filename, out_filename, dimensions, mode = params
    out_width, out_height = dimensions
    p_i('Generating %s' % out_filename)
    if mode == 'color':
        subprocess.call(['povray', '+W%d' % out_width, '+H%d' % out_height,
                         'Output_File_Type=N Bits_Per_Color=16 +Q4 +UR +A',
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
