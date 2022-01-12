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

    @app.route("/uploads/<filename>")
    def download_file(filename):
        return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

    @app.route("/rendering_dem")
    def rendering_dem():
        pano = request.args.get("pano")
        return render_template("rendering_dem.html", pano=pano)

    @app.route("/rendering")
    def rendering():
        pano = request.args.get("pano")
        app.logger.info(f"Rendering {pano}")
        render = render_dem(pano, 2, "")
        return redirect(url_for("render_preview", render=render))

    @app.route("/render_preview")
    def render_preview():
        render = request.args.get("render")
        return render_template("render_preview.html", render=render)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
