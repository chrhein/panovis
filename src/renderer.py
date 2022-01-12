import os
import time
import subprocess
from tools.debug import check_file_type, p_e, p_i, p_line
from location_handler import (
    find_visible_coordinates_in_render,
    get_mountains_in_sight,
    get_raster_data,
)
from map_plotting import plot_to_map
from povs import primary_pov, debug_pov
from tools.texture import (
    create_route_texture,
    create_color_gradient_image,
)
from tools.file_handling import get_mountain_data


def render_dem(panorama_path, mode, mountains):
    start_time = time.time()
    panorama_filename = panorama_path.split("/")[-1].split(".")[0]
    folder = "exports/%s/" % panorama_filename
    gpx_file = "data/hikes/%s.gpx" % panorama_filename

    try:
        os.mkdir(folder)
    except FileExistsError:
        pass

    dem_file, original_dem, coordinates = get_mountain_data(
        "data/dem-data.json", panorama_path
    )

    if mode == "debug":
        dem_file = original_dem

    if not check_file_type(dem_file):
        p_e("DEM file is not a valid GeoTIFF")
        return

    pov_filename = "/tmp/pov_file.pov"
    scale = 1.25
    render_shape = [4800 * scale, 800 * scale]

    raster_data = get_raster_data(dem_file, coordinates)
    if not raster_data:
        return

    ds_name = original_dem.split("/")[-1].split(".")[0]

    pov = [
        pov_filename,
        folder,
        render_shape,
    ]

    if mode == "debug":
        debug_mode = 2  # 1 for hike route texture
        if debug_mode == 1:
            route_texture, texture_bounds = create_route_texture(
                dem_file, gpx_file, True
            )
        else:
            route_texture, texture_bounds = "", None
        pov_filename, folder, _ = pov
        with open(pov_filename, "w") as pf:
            pov = debug_pov(dem_file, route_texture, texture_bounds, raster_data[1][2])
            pf.write(pov)
            pf.close()
        out_filename = f"{folder}{ds_name}-render-debug.png"
        params = [pov_filename, out_filename, [500, 500], "color"]
        execute_pov(params)
    else:
        pov_filename, folder, im_dimensions = pov
        if mode == 1:
            pov_mode = "depth"
            pov = primary_pov(dem_file, raster_data, mode=pov_mode)
            out_filename = f"{folder}{ds_name}-render-{pov_mode}.png"
            params = [pov_filename, out_filename, im_dimensions, pov_mode]
            with open(pov_filename, "w") as pf:
                pf.write(pov)
            pf.close()
            execute_pov(params)
        elif mode == 2:
            pov_mode = "height"
            pov = primary_pov(dem_file, raster_data, mode=pov_mode)
            out_filename = f"{folder}{ds_name}-render-{pov_mode}.png"
            params = [pov_filename, out_filename, im_dimensions, "color"]
            with open(pov_filename, "w") as pf:
                pf.write(pov)
            pf.close()
            execute_pov(params)
        elif mode == 3:
            pov_mode = "texture"
            gpx_exists = os.path.isfile("%s" % gpx_file)
            if gpx_exists:
                route_texture, texture_bounds = create_route_texture(dem_file, gpx_file)
                pov = primary_pov(
                    dem_file,
                    raster_data,
                    texture_path=route_texture,
                    tex_bounds=texture_bounds,
                    mode=pov_mode,
                )
                out_filename = f"{folder}{ds_name}-render-{pov_mode}.png"
                params = [pov_filename, out_filename, im_dimensions, "color"]
                with open(pov_filename, "w") as pf:
                    pf.write(pov)
                execute_pov(params)
            else:
                p_e("Could not find corresponding GPX")
                return
        elif mode == 4:
            pov_mode = "gradient"
            out_filename = f"{folder}{ds_name}-render-{pov_mode}.png"
            gradient_render = os.path.isfile("%s" % out_filename)
            gradient_path, _ = create_color_gradient_image()
            if not gradient_render:
                pov = primary_pov(
                    dem_file, raster_data, texture_path=gradient_path, mode=pov_mode
                )
                params = [pov_filename, out_filename, im_dimensions, pov_mode]
                with open(pov_filename, "w") as pf:
                    pf.write(pov)
                execute_pov(params)
            locs = find_visible_coordinates_in_render(
                ds_name, gradient_path, folder, dem_file
            )

            radius = 150  # in meters
            mountains_in_sight = get_mountains_in_sight(
                dem_file, locs, mountains, radius=radius
            )
            plot_filename = "%s%s.html" % (folder, panorama_filename)
            plot_to_map(
                mountains_in_sight,
                coordinates,
                plot_filename,
                dem_file,
                locs=locs,
                mountains=mountains,
                mountain_radius=radius,
            )
        else:
            return
    stats = [
        "Information about completed task: \n",
        "File:      %s" % panorama_filename,
        "Mode:      %s" % mode,
        "Duration:  %i seconds" % (time.time() - start_time),
    ]
    subprocess.call(["rm", "-r", "dev/cropped.png.aux.xml", "dev/cropped.png"])
    p_line(stats)


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