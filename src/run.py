import hashlib
import os
import pickle
import time
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from image_handling import (
    get_exif_gsp_img_direction,
    get_image_description,
    reduce_filesize,
    transform_panorama,
)
from renderer import mountain_lookup, render_height
from tools.file_handling import (
    get_files,
    get_seen_images,
    load_image_data,
    make_folder,
    save_image_data,
    trim_hikes,
)
from PIL import Image
from joblib import Parallel, delayed
from tools.types import ImageData

global UPLOAD_FOLDER
UPLOAD_FOLDER = "src/static/"

global DEBUG_HEIGHT
DEBUG_HEIGHT = False

global DEBUG_LOCATIONS
DEBUG_LOCATIONS = False

SEEN_IMAGES_PATH = f"{UPLOAD_FOLDER}dev/seen_images.txt"
SEEN_HIKES = f"{UPLOAD_FOLDER}hikes/"


def create_app():
    app = Flask(__name__, static_url_path=f"/{UPLOAD_FOLDER}")
    app.secret_key = "secret key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

    @app.route("/", methods=["POST", "GET"])
    def homepage():
        ims = get_seen_images()
        i = []
        for im in ims:
            im_data = load_image_data(im)
            if im_data:
                i.append([im_data.filename, im_data.thumbnail_path])
        gpx = session.get("gpx_path", "None selected")
        if gpx != "None selected":
            gpx = gpx.split("/")[-1]
        interactive = session.get("interactive", False)
        uploaded_hikes = [
            f"{x.split('/')[-1].split('.')[0]}" for x in get_files(SEEN_HIKES)
        ]

        return render_template(
            "home.html", ims=i, gpx=gpx, hikes=uploaded_hikes, folium=interactive
        )

    @app.route("/loading", methods=["POST", "GET"])
    def loading():
        redirect_url = request.args.get("redirect_url")
        task = request.args.get("task")
        title = request.args.get("title")
        text = request.args.get("text")
        return render_template(
            "loading.html", redirect_url=redirect_url, task=task, title=title, text=text
        )

    @app.route("/upload", methods=["POST", "GET"])
    def upload():

        if request.method == "POST":
            f = request.files["file"]
            filename = secure_filename(f.filename)
            f_hash = hashlib.md5(filename.encode("utf-8")).hexdigest()[-8:]
            fn, ft = filename.split(".")
            filename_h = f"{fn}-{f_hash}.{ft}"
            fp = f"{UPLOAD_FOLDER}images/"
            make_folder(fp)
            IMG_UPLOAD_FOLDER = f"{fp}{filename_h.split('.')[0]}/"
            session["img_folder"] = IMG_UPLOAD_FOLDER
            pano_path = f"{IMG_UPLOAD_FOLDER}{filename_h}"

            make_folder(UPLOAD_FOLDER)
            make_folder(IMG_UPLOAD_FOLDER)

            IMAGE_DATA = load_image_data(filename_h.split(".")[0])
            if IMAGE_DATA is None:
                IMAGE_DATA = ImageData(pano_path)
                save_image_data(IMAGE_DATA)

            session["filename"] = IMAGE_DATA.filename
            mark_image_seen(IMAGE_DATA)

            if not os.path.exists(IMAGE_DATA.path):
                f.save(IMAGE_DATA.path)
                reduce_filesize(IMAGE_DATA.path)

            im_view_direction = get_exif_gsp_img_direction(IMAGE_DATA.path)
            im_description = get_image_description(IMAGE_DATA.path)

            if im_view_direction is not None and im_description is not None:
                IMAGE_DATA.view_direction = im_view_direction
                save_image_data(IMAGE_DATA)

                if os.path.exists(IMAGE_DATA.render_path):
                    return redirect(url_for("homepage"))
            return redirect(url_for("spcoords"))

    @app.route("/uploadmtns", methods=["POST", "GET"])
    def uploadmtns():
        if request.method == "POST":
            f = request.files["file"]
            filename = secure_filename(f.filename)
            fp = f"{UPLOAD_FOLDER}gpx/"
            make_folder(fp)
            gpx_path = f"{fp}{filename}"
            session["gpx_path"] = gpx_path
            f.save(gpx_path)
            return redirect(url_for("homepage"))

    @app.route("/uploadhike", methods=["POST", "GET"])
    def uploadhike():
        if request.method == "POST":
            f = request.files["file"]
            app.logger.info(f)
            fp = f"{SEEN_HIKES}{f.filename}"
            session["hike"] = fp
            f.save(fp)
            return redirect(
                url_for(
                    "loading",
                    task="trimgpx",
                    title="Uploading Hike",
                    text="Uploading Hike ...",
                    redirect_url=url_for("homepage"),
                )
            )
        return redirect(url_for("homepage"))

    @app.route("/trimgpx")
    def trimgpx():
        f = session.get("hike", None)
        f_hash = hashlib.md5(f.encode("utf-8")).hexdigest()[-8:]
        fn = f.split("/")[-1].split(".")[0]
        filename_h = f"{fn}-{f_hash}"
        make_folder(SEEN_HIKES)
        trimmed = trim_hikes(f)
        hike_path = f"{SEEN_HIKES}{filename_h}.pkl"
        pickle.dump(trimmed, open(hike_path, "wb"))
        os.remove(f)
        return ("", 204)

    @app.route("/rmvimg", methods=["GET"])
    def rmvimg():
        file_to_remove = request.args.get("image_id")
        session["filename"] = remove_image_as_seen(file_to_remove)
        return redirect(url_for("homepage"))

    @app.route("/rmvhike", methods=["GET"])
    def rmvhike():
        file_to_remove = request.args.get("hike_id")
        remove_hike(file_to_remove)
        return redirect(url_for("homepage"))

    @app.route("/selectgpx", methods=["POST", "GET"])
    def selectgpx():
        return render_template("select_gpx.html")

    @app.route("/rendering")
    def rendering():
        IMAGE_DATA = load_image_data(get_filename())
        render_complete = render_height(IMAGE_DATA)
        if render_complete:
            return ("", 204)
        else:
            return "<h4>Render Failed</h4>"

    # select pano coordinates
    @app.route("/spcoords")
    def spcoords():
        IMAGE_DATA = load_image_data(get_filename())

        with Image.open(IMAGE_DATA.path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 750 * (height / width)
        vertical_fov = 250 * (height / width)
        return render_template(
            "pano_select_coords.html",
            pano_path=IMAGE_DATA.path,
            render_path=IMAGE_DATA.render_path,
            pwidth=width,
            pheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
        )

    # get pano selectec coordinates
    @app.route("/gpsc", methods=["POST"])
    def gpsc():
        IMAGE_DATA = load_image_data(get_filename())
        if request.method == "POST":
            pano_coords = request.form.get("pano-coords")
            pano_coords = strip_array(pano_coords)
            return redirect(
                url_for(
                    "srcoords",
                    render_path=IMAGE_DATA.render_path,
                    pano_coords=str(pano_coords),
                )
            )
        return ("", 404)

    # select render coordinates
    @app.route("/srcoords")
    def srcoords():
        IMAGE_DATA = load_image_data(get_filename())
        pano_coords = request.args.get("pano_coords")
        with Image.open(IMAGE_DATA.render_path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 360
        vertical_fov = 115
        return render_template(
            "render_select_coords.html",
            render_path=IMAGE_DATA.render_path,
            rwidth=width,
            rheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
            pano_coords=pano_coords,
        )

    # get render selected coordinates
    @app.route("/grsc", methods=["POST"])
    def grsc():
        if request.method == "POST":
            render_coords = request.form.get("render-coords")
            pano_coords = request.form.get("panorama-coords")
            return redirect(
                url_for(
                    "transform", render_coords=render_coords, pano_coords=pano_coords
                )
            )

    @app.route("/transform", methods=["POST", "GET"])
    def transform():
        IMAGE_DATA = load_image_data(get_filename())

        im_view_direction = get_exif_gsp_img_direction(IMAGE_DATA.path)
        session["filename"] = IMAGE_DATA.filename

        if im_view_direction is None:
            pano_coords = strip_array(request.args.get("pano_coords"), True)
            render_coords = strip_array(
                request.args.get("render_coords"), True)

            IMAGE_DATA = transform_panorama(
                IMAGE_DATA, pano_coords, render_coords)
            if not IMAGE_DATA:
                return "<h4>Transform failed because of an unequal amount of sample points in the panorama and render ...</h4>"

            save_image_data(IMAGE_DATA)
            session["filename"] = IMAGE_DATA.filename

        mark_image_seen(IMAGE_DATA)
        return render_template(
            "preview_warped.html",
            warped=IMAGE_DATA.overlay_path,
            render=IMAGE_DATA.ultrawide_path,
        )

    def mtn_lookup(pano_filename, gpx_path, interactive):
        im_data = load_image_data(pano_filename)
        if im_data is not None:
            mountains_3d, images_3d = mountain_lookup(
                im_data, gpx_path, interactive)
            gpx = gpx_path.split("/")[-1].split(".")[0]
            hs = create_hotspots(im_data, mountains_3d, images_3d)
            im_data.add_hotspots(gpx, hs)
            save_image_data(im_data)

    @app.route("/findmtns")
    def findmtns():
        gpx_path = session.get("gpx_path", None)
        if request.args.get("interactive", False) == "true":
            interactive = True
        else:
            interactive = False
        session["interactive"] = interactive
        seen_images = get_seen_images()
        fn = get_filename()
        session["filename"] = fn
        start_time = time.time()
        Parallel(n_jobs=min(4, len(seen_images)))(
            delayed(mtn_lookup)(pano_filename, gpx_path, interactive)
            for pano_filename in seen_images
        )
        app.logger.info(
            f"Duration:  {time.time() - start_time} seconds",
        )
        return ("", 204)

    @app.route("/mountains")
    def mountains():
        IMAGE_DATA = load_image_data(get_filename())
        gpx_filename = session.get(
            "gpx_path", None).split("/")[-1].split(".")[0]
        scenes = make_scenes(gpx_filename)
        interactive = session.get("interactive", False)
        return render_template(
            "view_mountains.html",
            scenes=scenes,
            defaultScene=IMAGE_DATA.filename,
            gpx=gpx_filename,
            interactive=interactive,
        )

    def get_filename():
        fn = session.get("filename", None)
        if fn is None:
            fn = get_seen_images()[-1]
        return fn

    return app


def mark_image_seen(img_data):
    if img_data.view_direction is None or img_data.hotspots is None:
        return
    make_folder(f"{UPLOAD_FOLDER}dev/")
    try:
        h = open(SEEN_IMAGES_PATH, "r")
        seen_images = h.readlines()
        h.close()
        if img_data.filename in seen_images or f"{img_data.filename}\n" in seen_images:
            return
        else:
            h = open(SEEN_IMAGES_PATH, "a")
            h.write(f"{img_data.filename}\n")
            h.close()

    except FileNotFoundError:
        print("An error occured when marking image as seen")


def remove_image_as_seen(image_filename):
    try:
        h = open(SEEN_IMAGES_PATH, "r")
        seen_images = h.readlines()
        if len(seen_images) == 1:
            h.close()
            os.remove(SEEN_IMAGES_PATH)
            return
        h.close()
        try:
            seen_images.remove(f"{image_filename}\n")
            w = open(SEEN_IMAGES_PATH, "w")
            w.writelines(seen_images)
            w.close()
        except ValueError:
            pass
        return seen_images[-1].strip("\n")
    except FileNotFoundError:
        pass


def remove_hike(hike_filename):
    try:
        os.remove(f"{SEEN_HIKES}/{hike_filename}.pkl")
    except FileNotFoundError:
        pass


def make_scenes(gpx_filename):
    seen_images = get_seen_images()
    scenes = {}
    for pano_filename in seen_images:
        im_data = load_image_data(pano_filename)
        if im_data is not None:
            hs_name = f"{im_data.filename}-{gpx_filename}"
            im_hs = im_data.hotspots.get(hs_name, None)
            if im_hs is not None:
                scenes[pano_filename] = {
                    "hotspots": im_hs,
                    "render_path": im_data.render_path,
                    "view_direction": im_data.view_direction,
                    "cropped_render_path": im_data.ultrawide_path,
                    "cropped_overlay_path": im_data.overlay_path,
                    "warped_panorama_path": im_data.warped_panorama_path,
                }
    return scenes


def create_hotspots(IMAGE_DATA, mountains_3d, images_3d):
    hotspots = {}
    mountain_hotpots = {}
    for mountain in mountains_3d:
        mountain_hotpots.update(
            {
                str(mountain.name): {
                    "yaw": IMAGE_DATA.view_direction
                    + float(mountain.location_in_3d.yaw),
                    "pitch": mountain.location_in_3d.pitch,
                    "distance": mountain.location_in_3d.distance,
                    "elevation": mountain.location.elevation,
                    "url": mountain.link,
                }
            }
        )
    image_hotpots = {}
    for image in images_3d:
        im_data = load_image_data(image.name)
        if im_data is not None:
            image_hotpots.update(
                {
                    str(image.name): {
                        "text": image.name[0:-9],
                        "imageTooltip": f"<div class='panorama-image-div'><img class='panorama-image' src='{im_data.thumbnail_path}'></div>",
                        "sceneId": image.name,
                        "yaw": IMAGE_DATA.view_direction
                        + float(image.location_in_3d.yaw),
                        "pitch": image.location_in_3d.pitch,
                        "distance": image.location_in_3d.distance,
                    }
                }
            )
    hotspots.update(
        {
            "mountains": mountain_hotpots,
            "images": image_hotpots,
        }
    )
    return hotspots


def strip_array(arr, to_pythonic_list=False):
    arr = [x.replace("[", "").replace("]", "") for x in arr.split("],")]
    a = []
    for i in arr:
        x, y = i.split(",")
        a.append(
            ((float(x), float(y))
             if to_pythonic_list else f"{float(x)}:{float(y)}")
        )
    return a


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
