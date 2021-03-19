# Digital Elevation Model to Depth Map

A script for rendering a depth map from a given digital elevation model (DEM).

## Example

Using a DEM for the southern parts of the Vestland region in Norway, which can be downloaded for free from [GeoNorge](https://kartkatalog.geonorge.no/nedlasting):

![Semi-RAW Digital Elevation File](assets/raw_dem.png)

In `main.py` I have specified that the coordinates I want to use as viewpoint is `60.36458, 5.32426`, which is the pair of latitude and longitude for the Løvstakken mountain in Bergen. Knowing that these coordinates are inside the bounds of the DEM, I can run the script with the downloaded DEM as an argument. This results in a generated PNG which contains the generated panorama image, looking like this:

![POV-Ray Result](assets/depth_map_example.png)
