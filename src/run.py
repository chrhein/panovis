from flask import Flask, render_template, request, redirect
from main import main


def create_app():
    app = Flask(__name__)
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
                return redirect(f"/dem")

    @app.route("/dem")
    def dem():
        return render_template("dem.html")

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="localhost", port=8080, debug=True)
    # main()
