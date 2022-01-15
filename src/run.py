import os
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    send_from_directory,
)

from renderer import render_dem


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
            pano = f"{UPLOAD_FOLDER}{f.filename}"
            f.save(pano)
            return redirect(url_for("rendering_dem", pano=pano))

    @app.route("/rendering_dem")
    def rendering_dem():
        pano_path = request.args.get("pano")
        pano_filename = f"{pano_path.split('/')[-1].split('.')[0]}"
        render_path = f"{UPLOAD_FOLDER}{pano_filename}-render.png"
        return render_template(
            "rendering_dem.html", pano_path=pano_path, render_path=render_path
        )

    @app.route("/rendering")
    def rendering():
        pano_path = request.args.get("pano_path")
        render_path = request.args.get("render_path")
        render_dem(pano_path, 2, "", render_filename=render_path)
        return ("", 204)

    @app.route("/render_preview")
    def render_preview():
        pano_path = request.args.get("pano_path")
        render_path = request.args.get("render_path")
        return render_template(
            "render_preview.html", pano_path=pano_path, render_path=render_path
        )

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
