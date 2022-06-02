from json import load
from dotenv import load_dotenv
import rasterio
from image_handling import transform_panorama
from location_handler import find_visible_items_in_ds
from map_plotting import plot_to_map
from renderer import generate_viewshed, render_height
from tools.debug import p_e
from tools.file_handling import get_mountain_data, load_image_data, read_image_locations, read_mountain_gpx
from tools.types import CrsToLatLng, LatLngToCrs
from vistools.tplot import plot_3d
from os import getenv


def debugger(mode):
    load_dotenv()
    if mode == 0:
        img_filename = getenv("DEBUG_IMAGE_FILENAME")
        img_data = load_image_data(img_filename)
        render_settings_path = "render_settings.json"
        with open(render_settings_path) as json_file:
            data = load(json_file)
            dem_path = data["dem_path"]
            json_file.close()
        dem_path, _, _ = get_mountain_data(
            dem_path, img_data, True
        )
        ds_raster = rasterio.open(dem_path)
        plotly_path = f"{img_data.folder}/{img_data.filename}-3d.html"
        plot_3d(ds_raster, plotly_path, True)
    elif mode == 1:
        img_filename = getenv("DEBUG_IMAGE_FILENAME")
        img_data = load_image_data(img_filename)
        render_settings_path = "render_settings.json"
        with open(render_settings_path) as json_file:
            data = load(json_file)
            dem_path = data["dem_path"]
            json_file.close()
        dem_path, coordinates, _ = get_mountain_data(
            dem_path, img_data, True
        )
        ds_raster = rasterio.open(dem_path)
        crs = int(ds_raster.crs.to_authority()[1])
        converter = LatLngToCrs(crs)
        viewshed = f'{img_data.folder}/viewshed.tif'
        ds_viewshed = rasterio.open(viewshed)
        gpx_file = getenv("DEBUG_GPX_FILE")
        mountains = read_mountain_gpx(gpx_file, converter)
        mountains_in_sight = find_visible_items_in_ds(
            ds_viewshed, mountains)
        plot_filename = f"{img_data.folder}/{img_data.filename}-{gpx_file.split('/')[-1].split('.')[0]}.html"
        images = read_image_locations(
            img_data.filename, "src/static/images", ds_raster, converter
        )
        plot_to_map(
            img_data.thumbnail_path,
            mountains_in_sight,
            coordinates,
            plot_filename,
            dem_path,
            CrsToLatLng(crs),
            mountains=mountains,
            images=images,
        )
    elif mode == 2:
        img_filename = getenv("DEBUG_IMAGE_FILENAME")
        img_data = load_image_data(img_filename)
        render_height(img_data, 400, True)
    elif mode == 3:
        pano_coords = [(1268.3492494885356, 521.1557312916943), (2232.240080844574, 809.9500084904776), (3366.9770353440626, 463.0411889003789),
                       (3436.3423840943774, 1079.8566784289249), (4197.845757610887, 846.6553426931105), (4856.037095186607, 568.4021607815313)]
        render_coords = [(803.8110237934407, 392.86419136189375), (989.3413003018161, 490.01350493066474), (1220.3083787348837, 367.32242148795035),
                         (1227.3717523122523, 634.7980082275224), (1362.7728783148518, 510.8354229634651), (1484.0790958974997, 408.3917555970175)]
        img_filename = getenv("DEBUG_IMAGE_FILENAME")
        img_data = load_image_data(img_filename)
        transform_panorama(img_data, pano_coords, render_coords)
    elif mode == 4:
        img_filename = getenv("DEBUG_IMAGE_FILENAME")
        img_data = load_image_data(img_filename)
        generate_viewshed(img_data)
    else:
        p_e("Mode not recognized")
