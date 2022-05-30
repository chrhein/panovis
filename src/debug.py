from json import load
from dotenv import load_dotenv
import rasterio
from location_handler import find_visible_items_in_ds
from map_plotting import plot_to_map
from tools.debug import p_e
from tools.file_handling import get_mountain_data, load_image_data, read_image_locations, read_mountain_gpx
from tools.types import CrsToLatLng, LatLngToCrs
from vistools.tplot import plot_3d
from os import getenv


def debugger(mode):
    if mode == 0:
        load_dotenv()
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
        load_dotenv()
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
    else:
        p_e("Mode not recognized")
