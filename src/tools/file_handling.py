import os
from map_plotting import compare_mtns_on_map
from tools.debug import p_i, p_in, p_line, p_e
from tkinter.filedialog import askopenfile, askopenfilenames
import tkinter as tk
import os
import gpxpy
import gpxpy.gpx
import rasterio
import image_handling
from location_handler import displace_camera, find_maximums, find_minimums, get_fov
from tools.converters import cor_to_crs
from tools.debug import p_i, p_line
from tools.types import Location, Mountain, MountainBounds
from osgeo import gdal


def get_mountain_data(dem_file, panorama_path, gradient=False):
    image_location = image_handling.get_exif_gps_latlon(panorama_path)
    if image_location:
        camera_lat, camera_lon = image_location.latitude, image_location.longitude
    else:
        p_e("No location data found in image. Exiting program.")
        return
    exif_view_direction = image_handling.get_exif_gsp_img_direction(panorama_path)
    if exif_view_direction and gradient:
        viewing_direction = exif_view_direction
        print(f"Viewing direction: {viewing_direction}")
    else:
        viewing_direction = 0.0
    look_ats = displace_camera(camera_lat, camera_lon, degrees=viewing_direction)

    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])

    camera_placement_crs = cor_to_crs(crs, camera_lat, camera_lon)

    displacement_distance = 15000  # in meters from camera placement

    bbox = (
        camera_placement_crs.GetX() - displacement_distance,
        camera_placement_crs.GetY() + displacement_distance,
        camera_placement_crs.GetX() + displacement_distance,
        camera_placement_crs.GetY() - displacement_distance,
    )

    coordinates = [camera_lat, camera_lon, *look_ats]

    cropped_dem = "dev/cropped.png"
    gdal.Translate(cropped_dem, dem_file, projWin=bbox)

    return [cropped_dem, dem_file, coordinates]


def read_hike_gpx(gpx_path):
    try:
        gpx_file = open(gpx_path, "r")
    except FileNotFoundError:
        return []
    gpx = gpxpy.parse(gpx_file)
    locations = [
        Location(k.latitude, k.longitude, k.elevation)
        for i in gpx.tracks
        for j in i.segments
        for k in j.points
    ]
    return [locations, find_minimums(locations), find_maximums(locations)]


def read_mountain_gpx(gpx_path):
    try:
        gpx_file = open(gpx_path, "r")
    except FileNotFoundError:
        return []
    gpx = gpxpy.parse(gpx_file)
    mountains = [
        Mountain(
            i.name,
            Location(i.latitude, i.longitude, i.elevation),
            MountainBounds(i.latitude, i.longitude),
        )
        for i in gpx.waypoints
    ]
    return mountains


def get_mountains(folder):
    files_in_folder = get_files(folder)
    mountain_dataset = {}
    info_title = "Select one of these files to continue:"
    input_text = "Select file: "
    error_text = "No valid file chosen."
    for i in range(len(files_in_folder)):
        file = files_in_folder[i].split("/")[-1]
        try:
            number_of_mountains_in_set = int(file.split("--")[0])
        except ValueError:
            continue
        mountain_name = file.split("--")[1].split(".")[0]
        mountain_dataset[mountain_name] = {
            "number_of_mountains": number_of_mountains_in_set,
            "file_name": files_in_folder[i],
        }
    mountain_dataset = dict(
        sorted(
            mountain_dataset.items(),
            key=lambda item: item[1].get("number_of_mountains"),
        )
    )
    info_text = [
        "%-38s size: %s"
        % (i[:35] + "..." if len(i) > 35 else i, str(j["number_of_mountains"]).rjust(3))
        for (i, j) in mountain_dataset.items()
    ]
    selected_file = tui_select(info_text, info_title, input_text, error_text)
    dataset = tuple(mountain_dataset.items())[selected_file - 1][1]["file_name"]
    p_i("%s was selected" % dataset.split("/")[-1])
    ds = {dataset: {"mountains": read_mountain_gpx(dataset)}}
    return ds


def compare_two_mountain_lists():
    folder = "data/mountains/"
    mtns_1 = get_mountains(folder)
    mtns_2 = get_mountains(folder)
    mn1 = list(mtns_1.values())[0]["mountains"]
    mn2 = list(mtns_2.values())[0]["mountains"]
    mtns_un_1 = sorted([i for i in mn1 if i not in mn2], key=lambda n: n.name)
    mtns_un_2 = sorted([i for i in mn2 if i not in mn1], key=lambda n: n.name)

    all_mtns = set(mn1 + mn2)

    ds = {list(mtns_1.keys())[0]: mtns_un_1, list(mtns_2.keys())[0]: mtns_un_2}

    key, val = list(ds.items())[0]
    t = ["Moutains unique to the following dataset:", "%s" % key.split("/")[-1]]
    p_line(t)
    p_line(["%-19s %-3s" % (i.name, str(int(i.location.elevation)) + "m") for i in val])
    f = "data/compared_ds/%s.html" % (
        list(mtns_1.keys())[0].split("/")[-1].split(".")[0]
        + "_"
        + list(mtns_2.keys())[0].split("/")[-1].split(".")[0]
    )
    compare_mtns_on_map(all_mtns, mn1, mn2, f)


def input_latlon():
    lat = float(input("Latitude: "))
    lon = float(input("Longitude: "))
    return lat, lon


def get_files(folder):
    file_list = os.listdir(folder)
    all_files = []
    for file in file_list:
        full_path = os.path.join(folder, file)
        if os.path.isdir(full_path):
            all_files = all_files + get_files(full_path)
        else:
            all_files.append(full_path)
    return all_files


def select_file(folder):
    files_in_folder = sorted(get_files(folder))
    info_text = []
    for i in range(len(files_in_folder)):
        file = files_in_folder[i].split("/")[-1]
        info_text.append("%i: %s" % (i + 1, file))
    info_text.append("0: exit program")
    p_i("Select one of these files to continue:")
    p_line(info_text)
    files_chosen = []
    while True:
        try:
            selected_file = p_in("Select file: ")
            selected_file = int(selected_file)
            exit() if selected_file == 0 else None
        except ValueError:
            try:
                x, y = selected_file.split("-")
                if min(int(x), int(y)) < 1 or max(int(x), int(y)) > len(info_text):
                    p_e("No valid file chosen.")
                    continue
                for i in range(min(int(x), int(y)), max(int(x) + 1, int(y) + 1)):
                    files_chosen.append(files_in_folder[i - 1])
                break
            except ValueError:
                p_e("No valid file chosen.")
            continue
        if selected_file < 1 or selected_file > len(info_text):
            p_e("No valid file chosen.")
            continue
        files_chosen.append(files_in_folder[selected_file - 1])
        break
    p_i("%s was selected" % str([i.split("/")[-1] for i in files_chosen]).strip("[]"))
    return files_chosen


def tui_select(it, itt="", in_t="", e_t="", afd=False):
    formatted_text = []
    for i in range(len(it)):
        formatted_text.append("%i: %s" % (i + 1, it[i]))
    formatted_text.append("0: exit")
    p_line()
    p_i(itt)
    p_line(formatted_text)
    while True:
        try:
            mode = p_in(in_t)
            if mode == "debug" and afd:
                return mode
            mode = int(mode)
        except ValueError:
            p_e(e_t)
            continue
        if mode == 0:
            exit()
        if mode < 1 or mode > len(it):
            p_e(e_t)
            continue
        return mode


def file_chooser(title, multiple=False):
    # Set environment variable
    os.environ["TK_SILENCE_DEPRECATION"] = "1"
    root = tk.Tk()
    root.withdraw()
    p_i("Opening File Explorer")
    if multiple:
        files = askopenfilenames(
            title=title,
            filetypes=[("PNGs", "*.png"), ("JPEGs", "*.jpeg"), ("JPGs", "*.jpg")],
        )
    else:
        filename = askopenfile(
            title=title,
            mode="r",
            filetypes=[("PNGs", "*.png"), ("JPEGs", "*.jpeg"), ("JPGs", "*.jpg")],
        )
    try:
        if multiple:
            p_i("%s was selected" % [i.split("/")[-1] for i in files])
            return files
        else:
            p_i("%s was selected" % filename.name.split("/")[-1])
            return filename.name
    except AttributeError:
        p_i("Exiting...")
        exit()


def make_folder(folder):
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass
