import pickle
import numpy as np
from tools.debug import p_i, p_in, p_line, p_e
import os
import gpxpy
import rasterio
import image_handling
import location_handler
from tools.types import Hike, ImageInSight, LatLngToCrs, Location, Mountain
from osgeo import gdal
from rdp import rdp


def get_mountain_data(dem_file, im_data, gradient=False):
    panorama_path = im_data.path
    image_location = image_handling.get_exif_gps_latlon(panorama_path)
    if image_location:
        camera_lat, camera_lon = image_location.latitude, image_location.longitude
    else:
        p_e("No location data found in image. Exiting program.")
        return
    exif_view_direction = image_handling.get_exif_gsp_img_direction(panorama_path)
    if exif_view_direction and gradient:
        viewing_direction = exif_view_direction
    else:
        viewing_direction = 0.0
    look_ats = location_handler.displace_camera(
        camera_lat, camera_lon, deg=viewing_direction
    )

    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])

    converter = LatLngToCrs(crs)
    camera_placement_crs = converter.convert(camera_lat, camera_lon)

    displacement_distance = 15000  # in meters from camera placement

    bbox = (
        camera_placement_crs.GetX() - displacement_distance,
        camera_placement_crs.GetY() + displacement_distance,
        camera_placement_crs.GetX() + displacement_distance,
        camera_placement_crs.GetY() - displacement_distance,
    )

    coordinates = [camera_lat, camera_lon, *look_ats]

    cropped_dem = f"dev/cropped-{im_data.filename}.png"
    gdal.Translate(cropped_dem, dem_file, projWin=bbox)

    return [cropped_dem, dem_file, coordinates, viewing_direction]


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
    return [
        locations,
        location_handler.find_minimums(locations),
        location_handler.find_maximums(locations),
    ]


def trim_hikes(gpx_file):
    gpx_f = open(gpx_file, "r")
    gpx = gpxpy.parse(gpx_f)
    locations = [
        [k.latitude, k.longitude, k.elevation]
        for i in gpx.tracks
        for j in i.segments
        for k in j.points
    ]
    trimmed = rdp(locations, epsilon=0.0001)
    return [Hike(gpx_file.split("/")[-1], [Location(x, y, z) for x, y, z in trimmed])]


def read_mountain_gpx(gpx_path, converter):
    try:
        gpx_file = open(gpx_path, "r")
    except FileNotFoundError:
        return []
    gpx = gpxpy.parse(gpx_file)
    mountains = []
    for i in gpx.waypoints:
        loc = Location(i.latitude, i.longitude, i.elevation)
        p = converter.convert(loc.latitude, loc.longitude, loc.elevation)
        loc2d = np.array((p.GetX(), p.GetY()))
        mountains.append(Mountain(i.name, loc, loc2d, link=i.link))
    return mountains


def read_image_locations(filename, image_folder, ds_raster, converter):
    locs = []
    seen_images = get_seen_images()
    for image in seen_images:
        if image == filename:
            continue
        im_path = f"{image_folder}/{image}/{image}.jpg"
        t_im_path = f"{image_folder}/{image}/{image}-thumbnail.jpg"
        loc = image_handling.get_exif_gps_latlon(im_path)
        height = location_handler.get_height_from_raster(loc, ds_raster, converter)
        loc = Location(loc.latitude, loc.longitude, height)
        p = converter.convert(loc.latitude, loc.longitude, loc.elevation)
        locs.append(ImageInSight(image, t_im_path, loc, np.array((p.GetX(), p.GetY()))))
    return locs


def get_files(folder):
    file_list = os.listdir(folder)
    all_files = []
    for file in file_list:
        if file == ".DS_Store":
            continue
        full_path = os.path.join(folder, file)
        if os.path.isdir(full_path):
            all_files = all_files + get_files(full_path)
        else:
            all_files.append(full_path)
    return all_files


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


def make_folder(folder):
    try:
        os.mkdir(folder)
    except FileExistsError:
        pass


def load_image_data(filename):
    fp = "src/static/images/"
    img_upload_folder = f"{fp}{filename.split('.')[0]}/"
    try:
        with open(f"{img_upload_folder}/{filename}-img-data.pkl", "rb") as f:
            img_data = pickle.load(f)
            f.close()
            if img_data is None:
                ims = get_seen_images()
                return load_image_data(ims[-1])
    except FileNotFoundError:
        return None
    return img_data


def save_image_data(img_data):
    with open(f"{img_data.folder}/{img_data.filename}-img-data.pkl", "wb") as f:
        pickle.dump(img_data, f)
    f.close()


def get_seen_images():
    try:
        ims = open("src/static/dev/seen_images.txt", "r")
        seen_images = [i.strip("\n") for i in ims.readlines()]
        ims.close()
        return seen_images
    except FileNotFoundError:
        return []
