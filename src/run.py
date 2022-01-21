import ast
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
)
from werkzeug.utils import secure_filename
from image_handling import (
    get_exif_data,
    reduce_filesize,
    transform_panorama,
)
from renderer import render_dem
from tools.file_handling import make_folder
from PIL import Image


def create_app():
    app = Flask(__name__, static_url_path="/src/static")
    UPLOAD_FOLDER = "src/static/"
    app.secret_key = "secret key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 30 * 1024 * 1024

    @app.route("/", methods=["POST", "GET"])
    def homepage():
        session["pano_path"] = ""
        session["render_path"] = ""
        session["render_coords"] = ""
        session["pano_coords"] = ""
        return render_template("upload_pano.html")

    @app.route("/upload", methods=["POST", "GET"])
    def upload():
        if request.method == "POST":
            f = request.files["file"]
            filename = secure_filename(f.filename)
            pano_path = f"{UPLOAD_FOLDER}{filename}"
            make_folder(UPLOAD_FOLDER)
            f.save(pano_path)
            reduce_filesize(pano_path)
            with Image.open(pano_path) as img:
                width, _ = img.size
                if width > 16384:
                    return "<h4>Image is too wide. Must be less than 16384px.</h4>"
                img.close()
            has_location_data = get_exif_data(pano_path)
            if not has_location_data:
                return "<h4>Image does not have location data.</h4>"
            session["pano_path"] = pano_path
            return redirect(url_for("spcoords"))

    @app.route("/rendering")
    def rendering():
        pano_path = session.get("pano_path", None)
        render_path = session.get("render_path", None)
        render_complete = render_dem(pano_path, 2, "", render_filename=render_path)
        if render_complete:
            return ("", 204)
        else:
            return "<h4>Render Failed</h4>"

    # select pano coordinates
    @app.route("/spcoords")
    def spcoords():
        pano_path = session["pano_path"]
        pano_filename = f"{pano_path.split('/')[-1].split('.')[0]}"
        render_path = f"{UPLOAD_FOLDER}{pano_filename}-render.png"
        session["render_path"] = render_path
        with Image.open(pano_path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 360 / (width / height)
        vertical_fov = 180 / (width / height)
        return render_template(
            "pano_select_coords.html",
            pano_path=pano_path,
            render_path=render_path,
            pwidth=width,
            pheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
        )

    # get pano selectec coordinates
    @app.route("/gpsc", methods=["POST"])
    def gpsc():
        if request.method == "POST":
            pano_coords = request.form.get("pano-coords")
            pano_coords = ast.literal_eval(pano_coords)
            session["pano_coords"] = pano_coords
            app.logger.info(f"pano_coords: {pano_coords}")
            render_path = session.get("render_path", None)
            return redirect(
                url_for(
                    "srcoords",
                    render_path=render_path,
                )
            )
        return ("", 404)

    # select render coordinates
    @app.route("/srcoords")
    def srcoords():
        render_path = session.get("render_path", None)
        with Image.open(render_path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 360
        vertical_fov = 115
        return render_template(
            "render_select_coords.html",
            render_path=render_path,
            rwidth=width,
            rheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
        )

    # get render selected coordinates
    @app.route("/grsc", methods=["POST"])
    def grsc():
        if request.method == "POST":
            render_coords = request.form.get("render-coords")
            render_coords = ast.literal_eval(render_coords)
            session["render_coords"] = render_coords
            app.logger.info(f"render_coords: {render_coords}")
            return redirect(url_for("transform"))

    @app.route("/transform")
    def transform():
        pano_path = session.get("pano_path", None)
        render_path = session.get("render_path", None)
        pano_coords = str(session.get("pano_coords", None))
        render_coords = str(session.get("render_coords", None))
        transformed_im, ultrawide_render = transform_panorama(
            pano_path, render_path, pano_coords, render_coords
        )
        return render_template(
            "preview_warped.html",
            warped=transformed_im,
            render=ultrawide_render,
        )

    """ @app.route("/testing")
    def testing():
        raw_coords = request.args.get("render_selected_coordinates")
        render_selected_coordinates = json.loads(raw_coords)
        app.logger.info(render_selected_coordinates)
        return ("", 204) """

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
