import ast
import json
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
)
from werkzeug.utils import secure_filename
from image_handling import reduce_filesize
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
            session["pano_path"] = pano_path
            return redirect(url_for("psc"))

    @app.route("/psc")
    def psc():
        pano_path = session["pano_path"]
        pano_filename = f"{pano_path.split('/')[-1].split('.')[0]}"
        render_path = f"{UPLOAD_FOLDER}{pano_filename}-render.png"
        session["render_path"] = render_path
        with Image.open(render_path) as img:
            width, height = img.size
            img.close()
        horizontal_fov = 120
        vertical_fov = 50
        return render_template(
            "pano_select_coords.html",
            pano_path=pano_path,
            render_path=render_path,
            pwidth=width,
            pheight=height,
            horizontal_fov=horizontal_fov,
            vertical_fov=vertical_fov,
        )

    @app.route("/rendering")
    def rendering():
        pano_path = session.get("pano_path", None)
        render_path = session.get("render_path", None)
        render_dem(pano_path, 2, "", render_filename=render_path)
        return ("", 204)

    @app.route("/rsc")
    def rsc():
        render_path = session.get("render_path", None)
        with Image.open(render_path) as img:
            width, height = img.size
            img.close()
        return render_template(
            "render_select_coords.html",
            render_path=render_path,
            rwidth=width,
            rheight=height,
        )

    @app.route("/save_pano_coordinates", methods=["POST"])
    def save_pano_coordinates():
        if request.method == "POST":
            pano_selected_coordinates = []
            req = request.form.get("panoCoords")
            req = ast.literal_eval(req)
            for x, y in req:
                pano_selected_coordinates.append({"x": x, "y": y})

            session["pano_selected_coordinates"] = json.dumps(
                pano_selected_coordinates, separators=(",", ":")
            )

            render_path = session.get("render_path", None)
            return redirect(
                url_for(
                    "rsc",
                    render_path=render_path,
                )
            )

    @app.route("/save_coordinates", methods=["POST"])
    def save_coordinates():
        if request.method == "POST":
            render_selected_coordinates = []
            req = request.form.get("coordinates")
            app.logger.info(req)
            """ render_selected_coordinates = [
                {"pitch": i[1], "yaw": i[0]} for i in req.split("")
            ] """
            req = ast.literal_eval(req)
            app.logger.info(req)

            for pitch, yaw in req:
                render_selected_coordinates.append({"pitch": pitch, "yaw": yaw})
                app.logger.info(f"Appending pitch: {pitch} and yaw: {yaw} to list.")
                app.logger.info(render_selected_coordinates)
            return redirect(
                url_for(
                    "testing",
                    render_selected_coordinates=json.dumps(
                        render_selected_coordinates, separators=(",", ":")
                    ),
                )
            )

    @app.route("/testing")
    def testing():
        raw_coords = request.args.get("render_selected_coordinates")
        render_selected_coordinates = json.loads(raw_coords)
        app.logger.info(render_selected_coordinates)
        return ("", 204)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
