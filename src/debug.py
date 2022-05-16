from json import load
from dotenv import load_dotenv
import rasterio
from tools.debug import p_e
from tools.file_handling import get_mountain_data, load_image_data
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
    else:
        p_e("Mode not recognized")
