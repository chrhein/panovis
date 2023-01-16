# PanoVis

### Installation

Clone the project, then run `pip install -r "requirements.txt"` to install all the necessary Python dependencies.
Additionally, [GDAL](https://gdal.org/download.html) and [POV-Ray](https://www.povray.org/download/) are required and can be downloaded either manually from their websites or through a packet manager like Homebrew for MacOS, using the following command:

`brew install gdal povray`

#### Setup

PanoVis requires a MapBox token for loading the visualizations that includes maps. Therefore, a MapBox token is required. This token should be added to an `.env` file located at root level, formatted as the following:

`MAPBOX_TOKEN=<your-token>`

Also, you can add custom MapBox styles by adding a valid MapBox Style URL to `.env` with the `MAPBOX_STYLE_URL` keyword.

A digital elevation model stored in a `.tiff` or `.dem` file is required for creating renderings and three-dimensional interactive terrain views. Please add this DEM to the project and update `render_settings.json` to reflect the path and filename of your DEM.

When running the application, it needs a `GPX` file containing the mountains that PanoVis should search for in the panoramas. These can be downloaded from [PeakBook](https://peakbook.org/) (might require a Pro subscription). This example can be used to create a file containing a single mountain:

```gpx
<?xml version="1.0" encoding="utf-8" standalone="no"?>
<gpx xmlns="http://www.topografix.com/GPX/1/1" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gpxx="http://www.garmin.com/xmlschemas/GpxExtensions/v3" xsi:schemaLocation="http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd http://www.garmin.com/xmlschemas/GpxExtensions/v3 http://www8.garmin.com/xmlschemas/GpxExtensionsv3.xsd" creator="Created by Peakbook. See http://peakbook.com" version="1.1"><wpt lon="5.3869462600603" lat="60.377480501152"><ele>643.0</ele><name>Ulriken</name><src>https://peakbook.org</src><link href="https://peakbook.org/peakbook-element/2260/Ulriken.html"/><sym>Summit</sym></wpt></gpx>
```


#### Running PanoVis

Start the flask server by running the `start` script. If everything is correctly setup, PanoVis will be running on `localhost:5000` waiting for you to upload your very first panorama to the application.
