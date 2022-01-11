import os
from flask import Flask, render_template, request, redirect, url_for
from main import main


def create_app():
    app = Flask(__name__, static_url_path="/static")
    UPLOAD_FOLDER = "static/uploads/"
    app.secret_key = "secret key"
    app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    main_modes = [
        "DEM Rendering",
        "Edge Detection",
        "Feature Matching",
        "Compare Datasets",
        "Previous Choices",
    ]

    @app.route("/")
    def homepage():
        return render_template("index.html", modes=main_modes)

    @app.route("/modes", methods=["POST", "GET"])
    def select_mode():
        if request.method == "POST":
            mode = int(request.form["mode-selector"]) - 1
            if mode == 0:
                return redirect(f"/panos")
            elif mode == 1:
                return redirect(f"/ed")
            elif mode == 2:
                return redirect(f"/fm")

    @app.route("/panos", methods=["POST", "GET"])
    def select_panorama():
        pics = sorted(os.listdir("src/static/panoramas/"))
        return render_template("photo_select.html", pics=pics)

    @app.route("/dem")
    def dem():
        return render_template("dem.html")

    @app.route("/ed")
    def ed():
        return render_template("ed.html")

    @app.route("/fm")
    def fm():
        return render_template("fm.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
