# PanoVis

### Installation

Clone the project, then run `pip install -r "requirements.txt"` to install all the necessary Python dependencies.
Additionally, [GDAL](https://gdal.org/download.html) and [POV-Ray](https://www.povray.org/download/) are required and can be downloaded either manually from their websites or through a packet manager like Homebrew for MacOS, using the following command:

`brew install gdal povray`

#### Setup

PanoVis requires a MapBox token for loading the visualizations that includes maps. Therefore, a MapBox token is required. This token should be added to an `.env` file located at root level, formatted as the following:

`MAPBOX_TOKEN=<your-token>`

Additionally, you can add custom MapBox styles by adding a valid MapBox Style URL to `.env` with the `MAPBOX_STYLE_URL` keyword.

A digital elevation model stored in a `.tiff` or `.dem` file is required for creating renderings and three-dimensional interactive terrain views. Please add this DEM to the project and update `render_settings.json` to reflect the path and filename of your DEM.

#### Running PanoVis

Start the flask server by running the `start` script. If everything is correctly setup, PanoVis will be running on `localhost:3000` waiting for you to upload your very first panorama to the application.
