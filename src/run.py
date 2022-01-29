import hashlib
import os
import pickle
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from image_handling import (
    get_exif_gsp_img_direction,
    get_image_description,
    reduce_filesize,
    transform_panorama,
)
from renderer import mountain_lookup, render_height
from tools.file_handling import make_folder
from PIL import Image

from tools.types import ImageData

global UPLOAD_FOLDER
UPLOAD_FOLDER = "src/static/"

global DEBUG_HEIGHT
DEBUG_HEIGHT = False


def create_app():
    app = Flask(__name__, static_url_path=f"/{UPLOAD_FOLDER}")
    app.secret_key = "secret key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

    @app.route("/", methods=["POST", "GET"])
    def homepage():
        return render_template("upload_pano.html")

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
            fp = f"{UPLOAD_FOLDER}images/"
            make_folder(fp)
            IMG_UPLOAD_FOLDER = f"{fp}{filename.split('.')[0]}/"
            session["img_folder"] = IMG_UPLOAD_FOLDER
            pano_path = f"{IMG_UPLOAD_FOLDER}{filename}"

            make_folder(UPLOAD_FOLDER)
            make_folder(IMG_UPLOAD_FOLDER)

            IMAGE_DATA = load_image_data(filename.split(".")[0])
            if IMAGE_DATA is None:
                IMAGE_DATA = ImageData(pano_path)
                img_key = hashlib.md5(filename.encode("utf-8")).hexdigest()
                IMAGE_DATA.hash = img_key
                save_image_data(IMAGE_DATA)

            session["filename"] = IMAGE_DATA.filename

            if not os.path.exists(IMAGE_DATA.path):
                f.save(IMAGE_DATA.path)
                reduce_filesize(IMAGE_DATA.path)
                """ hasher = hashlib.sha1()
                with open(IMAGE_DATA.path, "rb") as afile:
                    buf = afile.read(BLOCKSIZE)
                    while len(buf) > 0:
                        hasher.update(buf)
                        buf = afile.read(BLOCKSIZE)
                app.logger.info(hasher.hexdigest()) """

            if DEBUG_HEIGHT:
                return redirect(
                    url_for(
                        "loading",
                        redirect_url="srcoords",
                        task="rendering",
                        title="Rendering Height Image",
                        text="Rendering Height Image ...",
                    )
                )

            im_view_direction = get_exif_gsp_img_direction(IMAGE_DATA.path)
            im_description = get_image_description(IMAGE_DATA.path)

            if im_view_direction is not None and im_description is not None:
                if os.path.exists(IMAGE_DATA.render_path):
                    return redirect(url_for("selectgpx"))
            try:
                return redirect(url_for("spcoords"))
            except Exception as e:
                app.logger.error(e)
                return redirect(url_for("/"))

    @app.route("/uploadmtns", methods=["POST", "GET"])
    def uploadmtns():
        IMAGE_DATA = load_image_data(session.get("filename", None))
        if request.method == "POST":
            f = request.files["file"]
            filename = secure_filename(f.filename)
            fp = f"{UPLOAD_FOLDER}gpx/"
            make_folder(fp)
            gpx_path = f"{fp}{filename}"
            session["gpx_path"] = gpx_path
            f.save(gpx_path)

            gpx_filename = gpx_path.split("/")[-1].split(".")[0]
            hs_name = f"{IMAGE_DATA.filename}-{gpx_filename}"
            if hs_name in IMAGE_DATA.hotspots:
                return redirect(url_for("mountains"))

            redir_url = "mountains"
            task = "findmtns"
            title = "Locating Mountains"
            text = "Finding mountains in panorama..."
            return redirect(
                url_for(
                    "loading", redirect_url=redir_url, task=task, title=title, text=text
                )
            )

    @app.route("/selectgpx", methods=["POST", "GET"])
    def selectgpx():
        return render_template("select_gpx.html")

    @app.route("/rendering")
    def rendering():
        IMAGE_DATA = load_image_data(session.get("filename", None))
        render_complete = render_height(IMAGE_DATA)
        if render_complete:
            return ("", 204)
        else:
            return "<h4>Render Failed</h4>"

    # select pano coordinates
    @app.route("/spcoords")
    def spcoords():
        IMAGE_DATA = load_image_data(session.get("filename", None))

        with Image.open(IMAGE_DATA.path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 360 / (width / height)
        vertical_fov = 180 / (width / height)
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
        IMAGE_DATA = load_image_data(session.get("filename", None))
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
        IMAGE_DATA = load_image_data(session.get("filename", None))
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
        IMAGE_DATA = load_image_data(session.get("filename", None))

        im_view_direction = get_exif_gsp_img_direction(IMAGE_DATA.path)

        app.logger.info(im_view_direction)

        if im_view_direction is None:
            pano_coords = strip_array(request.args.get("pano_coords"), True)
            render_coords = strip_array(request.args.get("render_coords"), True)

            IMAGE_DATA = transform_panorama(IMAGE_DATA, pano_coords, render_coords)
            if not IMAGE_DATA:
                return "<h4>Transform failed because of an unequal amount of sample points in the panorama and render ...</h4>"

            save_image_data(IMAGE_DATA)
            add_hash(IMAGE_DATA.hash)
            session["filename"] = IMAGE_DATA.filename

        return render_template(
            "preview_warped.html",
            warped=IMAGE_DATA.overlay_path,
            render=IMAGE_DATA.ultrawide_path,
        )

    @app.route("/findmtns")
    def findmtns():
        IMAGE_DATA = load_image_data(session.get("filename", None))
        gpx_path = session.get("gpx_path", None)

        mountains_3d = mountain_lookup(IMAGE_DATA, gpx_path)
        hs = hotspots(mountains_3d)
        IMAGE_DATA.add_hotspots(hs)
        save_image_data(IMAGE_DATA)

        return redirect(url_for("mountains"))

    @app.route("/mountains")
    def mountains():
        IMAGE_DATA = load_image_data(session.get("filename", None))
        gpx_path = session.get("gpx_path", None)
        gpx_filename = gpx_path.split("/")[-1].split(".")[0]
        hs_name = f"{IMAGE_DATA.filename}-{gpx_filename}"
        hs = IMAGE_DATA.hotspots[hs_name]
        yaw = get_exif_gsp_img_direction(IMAGE_DATA.path)
        folium_path = f"{IMAGE_DATA.folder}/{hs_name}.html"
        return render_template(
            "view_mountains.html",
            hs=hs,
            render_path=IMAGE_DATA.render_path,
            yaw=yaw,
            folium_path=folium_path,
        )

    return app


def add_hash(img_hash):
    make_folder(f"{UPLOAD_FOLDER}dev/")
    hash_file = f"{UPLOAD_FOLDER}dev/hashes.txt"
    try:
        h = open(hash_file, "r")
        hashes = h.readlines()
        h.close()
        print(hashes)
        if img_hash in hashes:
            return
        else:
            h = open(hash_file, "a")
            h.write(f"{img_hash}\n")
            h.close()
    except FileNotFoundError:
        h = open(hash_file, "w")
        h.write(f"{img_hash}\n")
        h.close()


def save_image_data(img_data):
    with open(f"{img_data.folder}/{img_data.filename}-img-data.pkl", "wb") as f:
        pickle.dump(img_data, f)
    f.close()


def load_image_data(filename):
    fp = f"{UPLOAD_FOLDER}images/"
    IMG_UPLOAD_FOLDER = f"{fp}{filename.split('.')[0]}/"
    try:
        with open(f"{IMG_UPLOAD_FOLDER}/{filename}-img-data.pkl", "rb") as f:
            img_data = pickle.load(f)
    except FileNotFoundError:
        return None
    return img_data


def hotspots(mountains_3d):
    key, value = mountains_3d
    hotspots = {}
    for mountain in value.values():
        loc_3d = mountain.location_in_3d
        loc = mountain.location
        hotspots[mountain.name] = {
            "yaw": loc_3d.yaw,
            "pitch": loc_3d.pitch,
            "distance": loc_3d.distance,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
        }
    return [key, hotspots]


def strip_array(arr, to_pythonic_list=False):
    arr = [x.replace("[", "").replace("]", "") for x in arr.split("],")]
    a = []
    for i in arr:
        x, y = i.split(",")
        a.append(
            ((float(x), float(y)) if to_pythonic_list else f"{float(x)}:{float(y)}")
        )
    return a


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
