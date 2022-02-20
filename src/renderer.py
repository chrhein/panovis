from json import load
import os
import time
import subprocess
import rasterio
from tools.converters import convert_coordinates
from tools.debug import p_i, p_line
from location_handler import (
    create_viewshed,
    get_3d_location,
    find_visible_items_in_ds,
    get_raster_data,
)
from map_plotting import plot_to_map
from povs import primary_pov
from tools.file_handling import (
    get_mountain_data,
    read_image_locations,
    read_mountain_gpx,
)
from tools.types import CrsToLatLng, LatLngToCrs, Location


def render_height(img_data):
    if os.path.exists(img_data.render_path):
        return

    start_time = time.time()

    render_filename = img_data.render_path
    pov_filename = "/tmp/pov_file.pov"

    render_settings_path = "render_settings.json"
    with open(render_settings_path) as json_file:
        data = load(json_file)
        dem_path = data["dem_path"]
        r_width = data["render_width"]
        r_height = data["render_height"]

        render_shape = [r_width, r_height]
        json_file.close()

    dem_path, _, coordinates, _ = get_mountain_data(dem_path, img_data)

    ds_raster = rasterio.open(dem_path)
    raster_data = get_raster_data(ds_raster, coordinates)
    if not raster_data:
        return

    pov_mode = "height"
    pov = primary_pov(dem_path, raster_data, mode=pov_mode)
    params = [pov_filename, render_filename, render_shape, "color"]
    with open(pov_filename, "w") as pf:
        pf.write(pov)
    pf.close()

    converter = LatLngToCrs(int(ds_raster.crs.to_authority()[1]))
    locxy = converter.convert(coordinates[0], coordinates[1])
    create_viewshed(dem_path, (locxy.GetX(), locxy.GetY()), img_data.folder)

    execute_pov(params)
    stats = [
        "Information about completed task: \n",
        f"File:      {img_data.filename}",
        f"Mode:      {pov_mode}",
        f"Duration:  {time.time() - start_time} seconds",
    ]
    p_line(stats)
    return True


def mountain_lookup(img_data, gpx_file, plot=False):
    p_i(f"Beginning mountain lookup for {img_data.filename}")

    render_settings_path = "render_settings.json"
    with open(render_settings_path) as json_file:
        data = load(json_file)
        dem_path = data["dem_path"]
        json_file.close()

    dem_path, _, coordinates, viewing_direction = get_mountain_data(
        dem_path, img_data, True
    )

    ds_raster = rasterio.open(dem_path)
    crs = int(ds_raster.crs.to_authority()[1])
    lat, lon = coordinates[0], coordinates[1]

    converter = LatLngToCrs(crs)
    camera_height = convert_coordinates(
        ds_raster, converter, lat, lon, only_height=True
    )
    camera_location = Location(lat, lon, camera_height)

    viewshed = f'{img_data.folder}/viewshed.tif'
    ds_viewshed = rasterio.open(viewshed)

    images = read_image_locations(
        img_data.filename, "src/static/images", ds_raster, converter
    )
    images_in_sight = find_visible_items_in_ds(ds_viewshed, images)
    images_3d = get_3d_location(
        camera_location,
        viewing_direction,
        converter,
        images_in_sight,
    )

    mountains = read_mountain_gpx(gpx_file, converter)
    mountains_in_sight = find_visible_items_in_ds(
        ds_viewshed, mountains)
    mountains_3d = get_3d_location(
        camera_location,
        viewing_direction,
        converter,
        mountains_in_sight,
    )

    if plot:
        plot_filename = f"{img_data.folder}/{img_data.filename}-{gpx_file.split('/')[-1].split('.')[0]}.html"
        plot_to_map(
            img_data.thumbnail_path,
            mountains_3d,
            coordinates,
            plot_filename,
            dem_path,
            CrsToLatLng(crs),
            # locs=get_visible_coordinates(ds_raster, viewshed),
            mountains=mountains,
            images=images,
        )

    return mountains_3d, images_3d


def execute_pov(params):
    pov_filename, out_filename, dimensions, mode = params
    out_width, out_height = dimensions
    p_i("Generating %s" % out_filename)
    if mode == "color" or mode == "gradient":
        subprocess.call(
            [
                "povray",
                "+W%d" % out_width,
                "+H%d" % out_height,
                "Output_File_Type=N Bits_Per_Color=16 +Q8 +UR +A",
                "-GA",
                "+I" + pov_filename,
                "+O" + out_filename,
            ]
        )
    else:
        subprocess.call(
            [
                "povray",
                "+W%d" % out_width,
                "+H%d" % out_height,
                "Output_File_Type=N Bits_Per_Color=16 Display=off",
                "-GA",
                "Antialias=off Quality=0 File_Gamma=1.0",
                "+I" + pov_filename,
                "+O" + out_filename,
            ]
        )
