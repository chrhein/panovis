import pickle
from subprocess import call
import numpy as np
from tools.debug import p_a, p_i, p_in, p_line, p_e
import os
from pathlib import Path
import gpxpy
import rasterio
import image_handling
import location_handler
from tools.types import Hike, ImageInSight, LatLngToCrs, Location, Mountain, Waypoint
from rdp import rdp
from osgeo import gdal


def get_mountain_data(dem_file, im_data, gradient=False):
    panorama_path = im_data.path
    image_location = image_handling.get_exif_gps_latlon(panorama_path)
    if image_location:
        camera_lat, camera_lon = image_location.latitude, image_location.longitude
    else:
        p_e("No location data found in image. Exiting program.")
        return
    exif_view_direction = image_handling.get_exif_gsp_img_direction(
        panorama_path)
    if exif_view_direction and gradient:
        viewing_direction = exif_view_direction
    else:
        viewing_direction = 0.0
    look_ats = location_handler.displace_camera(
        camera_lat, camera_lon, deg=viewing_direction
    )
    coordinates = [camera_lat, camera_lon, *look_ats]
    ds_raster = rasterio.open(dem_file)
    crs = int(ds_raster.crs.to_authority()[1])

    converter = LatLngToCrs(crs)
    camera_placement_crs = converter.convert(camera_lat, camera_lon)

    displacement_distance = 20000  # in meters from camera placement

    westernmost_point = camera_placement_crs.GetX() - displacement_distance
    northernmost_point = camera_placement_crs.GetY() + displacement_distance
    easternmost_point = camera_placement_crs.GetX() + displacement_distance
    southernmost_point = camera_placement_crs.GetY() - displacement_distance

    ds_bbox = ds_raster.bounds
    if ds_bbox.left < westernmost_point:
        westernmost_point = ds_bbox.left
    if ds_bbox.right > easternmost_point:
        easternmost_point = ds_bbox.right
    if ds_bbox.top > northernmost_point:
        northernmost_point = ds_bbox.top
    if ds_bbox.bottom < southernmost_point:
        southernmost_point = ds_bbox.bottom

    bbox = (
        westernmost_point,
        northernmost_point,
        easternmost_point,
        southernmost_point,
    )
    tmp_ds = 'data/rasters/temp_dem.png'
    if dem_file.lower().endswith('.dem') or dem_file.lower().endswith('.tif'):
        call(['gdal_translate', '-ot', 'UInt16',
              '-of', 'PNG', dem_file, tmp_ds])
        dem_file = tmp_ds
    cropped_dem = f"data/rasters/cropped-{im_data.filename}.tif"
    gdal.Translate(cropped_dem, dem_file, projWin=bbox)
    return cropped_dem, coordinates


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


def trim_hike(gpx_file):
    ds_raster = rasterio.open(location_handler.get_raster_path())
    crs = int(ds_raster.crs.to_authority()[1])
    converter = LatLngToCrs(crs)
    gpx_f = open(gpx_file, "r")
    gpx = gpxpy.parse(gpx_f)
    locations = [
        [k.latitude, k.longitude, k.elevation]
        for i in gpx.tracks
        for j in i.segments
        for k in j.points
    ]
    trimmed = rdp(locations, epsilon=0.001)
    fn = gpx_file.split("/")[-1].split(".")[0]
    return Hike(gpx_file.split("/")[-1], [
        Waypoint(f"{fn}{i}",
                 Location(*val),
                 np.array((converter.convert(*val).GetPoints()[0])))
        for i, val in enumerate(trimmed)
    ])


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
    seen_images = get_seen_items('images')
    for image in seen_images:
        if image == filename:
            continue
        im_path = f"{image_folder}/{image}/{image}.jpg"
        t_im_path = f"{image_folder}/{image}/{image}-thumbnail.jpg"
        loc = image_handling.get_exif_gps_latlon(im_path)
        height = location_handler.get_height_from_raster(
            loc, ds_raster, converter)
        loc = Location(loc.latitude, loc.longitude, height)
        p = converter.convert(loc.latitude, loc.longitude, loc.elevation)
        locs.append(ImageInSight(image, t_im_path, loc,
                    np.array((p.GetX(), p.GetY()))))
    return locs


def get_files(folder):
    make_folder(folder)
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
                ims = get_seen_items('images')
                return load_image_data(ims[-1])
    except FileNotFoundError:
        return None
    return img_data


def save_image_data(img_data):
    with open(f"{img_data.folder}/{img_data.filename}-img-data.pkl", "wb") as f:
        pickle.dump(img_data, f)
    f.close()


def get_seen_items(kind="images"):
    try:
        ims = open(f"src/static/dev/seen_{kind}.txt", "r")
        seen_images = [i.strip("\n") for i in ims.readlines()]
        ims.close()
        return seen_images
    except FileNotFoundError:
        return []


def get_hikes():
    h_path = "src/static/hikes"
    hikes = get_files(h_path)
    for h in hikes:
        l_hike = pickle.load(open(h, "rb"))[0]
        yield l_hike


def reset_image(im):
    p_i(f"Resetting image {im}")
    IMAGE_DATA = load_image_data(im)
    try:
        os.remove(IMAGE_DATA.overlay_path)
    except (AttributeError, FileNotFoundError):
        pass
    try:
        os.remove(IMAGE_DATA.ultrawide_path)
    except (AttributeError, FileNotFoundError):
        pass
    try:
        os.remove(IMAGE_DATA.warped_panorama_path)
    except (AttributeError, FileNotFoundError):
        pass
    IMAGE_DATA.view_direction = None
    IMAGE_DATA.fov_l = None
    IMAGE_DATA.fov_r = None
    IMAGE_DATA.location = None
    IMAGE_DATA.transform_matrix = None
    save_image_data(IMAGE_DATA)


def remove_with_force(im):
    try:
        def remove_path(path: Path):
            if path.is_file() or path.is_symlink():
                path.unlink()
                return
            for p in path.iterdir():
                remove_path(p)
            path.rmdir()
        path_to_remove = Path(f"src/static/images/{im}")
        remove_path(path_to_remove)
        p_a(f"Removed image {im}")
    except (FileNotFoundError):
        pass
