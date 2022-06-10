import pickle
from json import load
import os
import time
import subprocess
from dotenv import load_dotenv
import rasterio
import requests
from tools.converters import convert_coordinates
from tools.debug import p_e, p_i, p_line
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
    save_image_data,
)
from tools.types import CrsToLatLng, LatLngToCrs, Location
from vistools.tplot import plot_3d
from requests.structures import CaseInsensitiveDict


def render_height(img_data, r_h=None, debug=False):
    if os.path.exists(img_data.render_path) and not debug:
        return
    start_time = time.time()
    render_filename = img_data.render_path
    pov_filename = "/tmp/pov_file.pov"
    render_settings_path = "render_settings.json"
    with open(render_settings_path) as json_file:
        data = load(json_file)
        dem_file = data["dem_path"]
        if r_h:
            render_shape = [r_h*2, r_h]
        else:
            r_width = data["render_width"]
            r_height = data["render_height"]
            render_shape = [r_width, r_height]
        json_file.close()

    cropped_dem, coordinates, image_location = get_mountain_data(
        dem_file, img_data)
    ds_raster = rasterio.open(cropped_dem)
    raster_data, elevation = get_raster_data(ds_raster, coordinates)
    if not raster_data:
        return
    pickle.dump([cropped_dem, coordinates, image_location, elevation], open(
        f"{img_data.folder}/vs.pkl", "wb"))
    pov_mode = "height"
    pov = primary_pov(cropped_dem, raster_data, mode=pov_mode)
    params = [pov_filename, render_filename, render_shape, "color"]
    with open(pov_filename, "w") as pf:
        pf.write(pov)
    pf.close()
    print(f"Rendering {render_filename}")
    execute_pov(params)
    stats = [
        "Information about completed task: \n",
        f"File:      {img_data.filename}",
        f"Mode:      {pov_mode}",
        f"Duration:  {time.time() - start_time} seconds",
    ]
    p_line(stats)
    return True


def generate_viewshed(img_data):
    cropped_dem, coordinates, image_location, elevation = pickle.load(
        open(f"{img_data.folder}/vs.pkl", "rb"))
    ds_raster = rasterio.open(cropped_dem)
    p_i(f"Creating viewshed for {img_data.filename}")
    converter = LatLngToCrs(int(ds_raster.crs.to_authority()[1]))
    locxy = converter.convert(coordinates[0], coordinates[1])
    vs_created = create_viewshed(cropped_dem, (locxy.GetX(),
                                               locxy.GetY()), img_data.folder)
    if not vs_created:
        p_e(f"Failed to create viewshed for {img_data.filename}")
        return False
    load_dotenv()
    api_key = os.getenv("MAPBOX_TOKEN")
    url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{image_location.longitude},{image_location.latitude}.json?access_token={api_key}"
    headers = CaseInsensitiveDict()
    headers["Accept"] = "application/json"
    resp = requests.get(url, headers=headers).json()
    place_name = resp["features"][0]["text"]
    img_data.place_name = place_name
    img_data.place_elevation = elevation
    save_image_data(img_data)
    return True


def mountain_lookup(img_data, gpx_file, plot=False):
    p_i(f"Beginning mountain lookup for {img_data.filename}")

    viewshed = f'{img_data.folder}/viewshed.tif'
    ds_viewshed = rasterio.open(viewshed)
    if not ds_viewshed:
        return False

    render_settings_path = "render_settings.json"
    with open(render_settings_path) as json_file:
        data = load(json_file)
        dem_file = data["dem_path"]
        json_file.close()

    cropped_dem, coordinates, _, _ = pickle.load(
        open(f"{img_data.folder}/vs.pkl", "rb"))

    ds_raster = rasterio.open(cropped_dem)
    crs = int(ds_raster.crs.to_authority()[1])
    lat, lon = coordinates[0], coordinates[1]

    converter = LatLngToCrs(crs)
    camera_height = convert_coordinates(
        ds_raster, converter, lat, lon, True
    )
    camera_location = Location(lat, lon, camera_height)

    viewshed = f'{img_data.folder}/viewshed.tif'
    ds_viewshed = rasterio.open(viewshed)

    """ visible_hikes = {}
    for hike in get_hikes():
        waypoints_in_sight = find_visible_items_in_ds(
            ds_viewshed, hike.waypoints
        )
        waypoints_3d = get_3d_location(
            camera_location,
            waypoints_in_sight,
        )
        visible_hikes[hike.name] = waypoints_3d """

    images = read_image_locations(
        img_data.filename, "src/static/images", ds_raster, converter
    )
    images_in_sight = find_visible_items_in_ds(ds_viewshed, images)
    images_3d = get_3d_location(
        camera_location,
        images_in_sight,
    )

    mountains = read_mountain_gpx(gpx_file, converter)
    mountains_in_sight = find_visible_items_in_ds(
        ds_viewshed, mountains)
    mountains_3d = get_3d_location(
        camera_location,
        mountains_in_sight,
    )

    if plot:
        plotly_path = f"{img_data.folder}/{img_data.filename}-3d.json"
        if not os.path.exists(plotly_path):
            plot_3d(ds_raster, plotly_path)

        plot_filename = f"{img_data.folder}/{img_data.filename}-{gpx_file.split('/')[-1].split('.')[0]}.html"
        plot_to_map(
            img_data.thumbnail_path,
            mountains_3d,
            coordinates,
            plot_filename,
            dem_file,
            CrsToLatLng(crs),
            mountains=mountains,
            images=images,
        )

    return mountains_3d, images_3d, {}


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
