import cv2
import os
import subprocess
from geopy import distance
from datetime import datetime
from feature_matching import feature_matching
from edge_detection import edge_detection
from data_getters.mountains import get_mountain_data, get_mountain_list
from colors import color_interpolator, get_color_from_image
from data_getters.raster import get_raster_data
from debug_tools import p_e, p_i, p_line
from location_handler import coordinate_lookup, crs_to_wgs84, plot_to_map
from povs import color_gradient_pov, depth_pov, height_pov, texture_pov, debug_pov
from tools.types import Texture, Location
from tools.color_map import create_route_texture


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

    # gpx_path = "data/%s.gpx" % filename
    # read_gpx(gpx_path)

    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

    cv2.imwrite(('%s%s.png' % (folder, filename)), cv2.resize(img, [new_width, new_height]))

    pov_filename = '/tmp/pov_file.pov'
    im_dimensions = [out_width, out_height]
    raster_data = get_raster_data(dem_file, coordinates, pov_settings[1])
    pov = [pov_filename, folder, im_dimensions, pov_settings]
    pov_params = [dem_file, pov, raster_data]

    if mode == 'debug':
        route_texture, texture_bounds = create_route_texture(dem_file, gpx_file)
        debug_texture(dem_file, route_texture, texture_bounds, pov, raster_data[1][3])
    elif mode == 1:
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
        get_coordinates_in_image(dem_file, pano, coordinates, folder, filename)
    elif mode == 8:
        route_texture, texture_bounds = create_route_texture(dem_file, gpx_file)
        if route_texture:
            pov_params[1][3].append(route_texture)
            pov_params[1][3].append(texture_bounds)
            scaled_coordinates = raster_data[0]
            camera_location = Location(
                latitude=scaled_coordinates[0],
                longitude=scaled_coordinates[2],
                elevation=scaled_coordinates[1]
            )
            viewpoint_location = Location(
                latitude=scaled_coordinates[3],
                longitude=scaled_coordinates[5],
                elevation=scaled_coordinates[4]
            )
            tex = Texture(
                dem=dem_file,
                texture=route_texture,
                camera=camera_location,
                viewpoint=viewpoint_location,
                angle=120,
                scale=0.75,
                bounds=texture_bounds
            )
            create_texture_image(*pov_params)
        else:
            p_e('Could not find corresponding GPX')


def get_coordinates_in_image(dem_file, pano, coordinates, folder, filename):
    loc_x = os.path.isfile('%srender-loc_x.png' % folder)
    loc_z = os.path.isfile('%srender-loc_z.png' % folder)
    loc_files_exist = loc_x and loc_z
    if not loc_files_exist:
        render_dem(pano, 4)
    file_exist = os.path.isfile('%slocations.txt' % folder)
    # file_exist = False
    if file_exist:
        file = open('%slocations.txt' % folder, 'r')
        locs = [line.rstrip() for line in file.readlines()]
        file.close()
        locs = [(float(i[0]), float(i[1]))
                for i in (x.split(',') for x in locs)]
    else:
        start_time = datetime.now()
        im1 = cv2.cvtColor(cv2.imread('%srender-loc_x.png' % folder),
                           cv2.COLOR_BGR2RGB)
        im2 = cv2.cvtColor(cv2.imread('%srender-loc_z.png' % folder),
                           cv2.COLOR_BGR2RGB)
        locs = coordinate_lookup(im1, im2, dem_file)
        file = open('%slocations.txt' % folder, 'w')
        [file.write('%s\n' % str(i).strip('()')) for i in locs]
        file.close()
        end_time = datetime.now()
        dur = end_time - start_time
        p_i('Total runtime: %s seconds' % str(dur.seconds))
    p_line(includes_mountain(locs))
    plot_filename = '%s%s.html' % (folder, filename)
    plot_to_map(locs, coordinates, plot_filename)


def includes_mountain(locs):
    mountains = get_mountain_list('data/dem-data.json')
    mountains_in_sight = set()
    radius = 500
    for pos in locs:
        lat, lon = pos
        for mountain in mountains:
            m = mountain.location
            m_lat, m_lon = m.latitude, m.longitude
            center_point = [{'lat': m_lat, 'lng': m_lon}]
            test_point = [{'lat': lat, 'lng': lon}]
            center_point = tuple(center_point[0].values())
            test_point = tuple(test_point[0].values())
            dis = distance.distance(center_point, test_point).m
            if dis <= radius:
                mountains_in_sight.add(mountain.name)
    return mountains_in_sight


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


def create_texture_image(dem_file, pov, raster_data):
    # generating pov-ray render with image texture map
    pov_filename, folder, im_dimensions, pov_settings = pov
    with open(pov_filename, 'w') as pf:
        pov = texture_pov(dem_file, raster_data, pov_settings)
        pf.write(pov)
        pf.close()
    out_filename = '%srender-texture.png' % folder
    params = [pov_filename, out_filename, im_dimensions, 'color']
    execute_pov(params)
    '''
    height = '%srender-height.png' % folder
    background = cv2.imread(height)
    overlay = cv2.imread(out_filename)
    tmp = cv2.cvtColor(overlay, cv2.COLOR_BGR2GRAY)
    _, alpha = cv2.threshold(tmp, 0, 255, cv2.THRESH_BINARY)
    b, g, r = cv2.split(overlay)
    rgba = [b, g, r, alpha]
    overlay = cv2.merge(rgba, 4)
    super = '%srender-merged.png' % folder
    x1, y1, x2, y2 = 0, 0, background.shape[1], background.shape[0]
    background[y1:y2, x1:x2] = background[y1:y2, x1:x2] * \
        (1 - overlay[:, :, 3:] / 255) + \
        overlay[:, :, :3] * (overlay[:, :, 3:] / 255)
    cv2.imwrite(super, background)
    '''


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
    x_colors = color_interpolator(0, 255, int(total_distance_n_s))
    y_colors = color_interpolator(255, 0, int(total_distance_e_w))
    z_index = x_colors.index(color_x[0])
    x_index = y_colors.index(color_z[0])

    x, y = ds_raster.xy(x_index / resolution, z_index / resolution)

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
