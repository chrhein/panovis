import os
import pickle
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from image_handling import (
    get_exif_gps_latlon,
    get_exif_gsp_img_direction,
    get_image_description,
    reduce_filesize,
    transform_panorama,
)
from renderer import mountain_lookup, render_height
from tools.file_handling import make_folder
from PIL import Image
import hashlib

from tools.types import ImageData

global UPLOAD_FOLDER
UPLOAD_FOLDER = "src/static/"

global IMG_UPLOAD_FOLDER
IMG_UPLOAD_FOLDER = None

global GPX_UPLOAD_FOLDER
GPX_UPLOAD_FOLDER = f"{UPLOAD_FOLDER}gpx/"

global HASH_LIST
HASH_LIST = f"{UPLOAD_FOLDER}hash_list.txt"

global DEBUG_HEIGHT
DEBUG_HEIGHT = False

global BLOCKSIZE
BLOCKSIZE = 65536

global IMAGE_DATA
IMAGE_DATA = None


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
        global IMAGE_DATA
        global IMG_UPLOAD_FOLDER

        if request.method == "POST":

            f = request.files["file"]
            filename = secure_filename(f.filename)
            if not IMG_UPLOAD_FOLDER:
                fp = f"{UPLOAD_FOLDER}images/"
                IMG_UPLOAD_FOLDER = f"{fp}{filename.split('.')[0]}/"
            pano_path = f"{IMG_UPLOAD_FOLDER}{filename}"

            make_folder(UPLOAD_FOLDER)
            make_folder(IMG_UPLOAD_FOLDER)

            IMAGE_DATA = ImageData(pano_path)
            session["img_data"] = IMAGE_DATA

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

            if im_view_direction and im_description:
                if os.path.exists(IMAGE_DATA.render_path):
                    return redirect(url_for("selectgpx"))

            return redirect(url_for("spcoords"))

    @app.route("/uploadmtns", methods=["POST", "GET"])
    def uploadmtns():
        if request.method == "POST":
            f = request.files["file"]
            filename = secure_filename(f.filename)
            gpx_path = f"{GPX_UPLOAD_FOLDER}{filename}"
            make_folder(GPX_UPLOAD_FOLDER)
            f.save(gpx_path)
            app.logger.info(f"Saved {filename}")
            session["gpx_path"] = gpx_path
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
        get_image_data()
        render_complete = render_height(IMAGE_DATA)
        if render_complete:
            return ("", 204)
        else:
            return "<h4>Render Failed</h4>"

    # select pano coordinates
    @app.route("/spcoords")
    def spcoords():
        get_image_data()

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
        get_image_data()
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
        get_image_data()
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
        get_image_data()

        pano_coords = strip_array(request.args.get("pano_coords"), True)
        render_coords = strip_array(request.args.get("render_coords"), True)

        transform_complete = transform_panorama(IMAGE_DATA, pano_coords, render_coords)

        if not transform_complete:
            return "<h4>Transform failed because of an unequal amount of sample points in the panorama and render ...</h4>"
        return render_template(
            "preview_warped.html",
            warped=IMAGE_DATA.overlay_path,
            render=IMAGE_DATA.ultrawide_path,
        )

    @app.route("/findmtns")
    def findmtns():
        get_image_data()

        gpx_path = session.get("gpx_path", None)

        make_folder(f"{UPLOAD_FOLDER}/locs/{IMAGE_DATA.filename}/")
        gpx_filename = gpx_path.split("/")[-1].split(".")[0]

        hs_path = f"{UPLOAD_FOLDER}/locs/{IMAGE_DATA.filename}/{IMAGE_DATA.filename}-{gpx_filename}.pkl"

        session["hs_path"] = hs_path

        if not os.path.exists(hs_path):
            mountains_3d = mountain_lookup(
                IMAGE_DATA.path, IMAGE_DATA.gradient_path, gpx_path
            )
            hs = hotspots(mountains_3d)
            with open(hs_path, "wb") as f:
                pickle.dump(hs, f)

        return redirect(url_for("mountains"))

    @app.route("/mountains")
    def mountains():
        get_image_data()

        hs_path = session.get("hs_path", None)
        with open(hs_path, "rb") as f:
            hs = pickle.load(f)
            app.logger.info(f"hotspots: {hs}")
        yaw = get_exif_gsp_img_direction(IMAGE_DATA.path)
        return render_template(
            "view_mountains.html",
            hs=hs,
            render_path=IMAGE_DATA.render_path,
            yaw=yaw,
            pano_filename=IMAGE_DATA.filename,
        )

    def get_image_data():
        global IMAGE_DATA
        im_data = session.get("img_data", None)
        app.logger.info(f"img_data: {im_data}")
        i = ImageData(im_data["path"])
        i.view_direction = im_data["view_direction"]
        i.fov_l = im_data["fov_l"]
        i.fov_r = im_data["fov_r"]
        i.im_dimensions = im_data["im_dimensions"]
        i.coordinates = im_data["coordinates"]
        IMAGE_DATA = i

    return app


def hotspots(mountains_3d):
    hotspots = {}
    for mountain in mountains_3d.values():
        loc_3d = mountain.location_in_3d
        loc = mountain.location
        hotspots[mountain.name] = {
            "yaw": loc_3d.yaw,
            "pitch": loc_3d.pitch,
            "distance": loc_3d.distance,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
        }
    print(hotspots)
    return


def strip_array(arr, to_pythonic_list=False):
    arr = [x.replace("[", "").replace("]", "") for x in arr.split("],")]
    a = []
    for i in arr:
        x, y = i.split(",")
        a.append(
            ((float(x), float(y)) if to_pythonic_list else f"{float(x)}:{float(y)}")
        )
    print(a)
    return a


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
