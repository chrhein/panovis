from image_handling import rotate_image_on_map
from dotenv import load_dotenv
import folium, folium.raster_layers
import os
import cv2
from location_handler import get_raster_bounds
from tools.debug import p_i


def plot_to_map(
    mountains_in_sight,
    coordinates,
    filename,
    dem_file,
    locs=[],
    mountains=[],
    mountain_radius=150,
):
    p_i("Creating Interactive Map")
    c_lat, c_lon, _, _ = coordinates
    ll, ul, ur, lr = get_raster_bounds(dem_file)
    load_dotenv()
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
    MAPBOX_STYLE_URL = os.getenv("MAPBOX_STYLE_URL")
    m = folium.Map([c_lat, c_lon], tiles=None, zoom_start=12)
    folium.TileLayer(
        location=[c_lat, c_lon],
        tiles=MAPBOX_STYLE_URL,
        API_key=MAPBOX_TOKEN,
        attr="Christian Hein",
        name="Map",
    ).add_to(m)

    if mountains:
        mountains_fg = folium.FeatureGroup(name="All Mountains", show=False)
        m.add_child(mountains_fg)
        [
            (
                folium.Circle(
                    location=(i.location.latitude, i.location.longitude),
                    color="#ed6952",
                    fill=True,
                    fill_color="#ed6952",
                    fill_opacity=0.2,
                    radius=mountain_radius,
                    popup=f"{i.name}, {int(i.location.elevation)} m",
                ).add_to(mountains_fg)
            )
            for i in mountains
        ]
    if mountains_in_sight:
        mountains_in_sight_fg = folium.FeatureGroup(
            name="Mountains In-Sight", show=True
        )
        m.add_child(mountains_in_sight_fg)
        [
            (
                folium.Marker(
                    location=(i.location.latitude, i.location.longitude),
                    popup="%s\n%.4f, %.4f\n%im"
                    % (
                        str(i.name),
                        i.location.latitude,
                        i.location.longitude,
                        i.location.elevation,
                    ),
                    icon=folium.Icon(color="pink", icon="mountain"),
                ).add_to(mountains_in_sight_fg)
            )
            for i in mountains_in_sight.values()
        ]

    folium.Marker(
        location=[c_lat, c_lon],
        popup="Camera Location",
        icon=folium.Icon(color="green", icon="camera"),
    ).add_to(m)

    if locs:
        locs_fg = folium.FeatureGroup(name="Retrieved Coordinates", show=True)
        m.add_child(locs_fg)
        [
            (
                folium.Circle(
                    location=(i.latitude, i.longitude),
                    color="#0a6496",
                    fill=True,
                    fill_color="#0a6496",
                    fill_opacity=1,
                    radius=15,
                ).add_to(locs_fg)
            )
            for i in locs
        ]

    raster_bounds = folium.FeatureGroup(name="Raster Bounds", show=True)
    m.add_child(raster_bounds)
    folium.PolyLine(locations=[ll, ul, ur, lr, ll], color="#ed6952").add_to(
        raster_bounds
    )

    lower_left, upper_left, upper_right, lower_right = get_raster_bounds(dem_file)

    ll1, _ = lower_left
    _, ul2 = upper_left
    ur1, _ = upper_right
    _, lr2 = lower_right

    color_gradient = folium.FeatureGroup(
        name="Color Gradient (Not Working)", show=False
    )
    m.add_child(color_gradient)
    im = cv2.imread("data/color_gradient.png")
    rotated_image = rotate_image_on_map(im, lower_left, upper_left)

    folium.raster_layers.ImageOverlay(
        image=rotated_image,
        bounds=[(ll1, ul2), (ur1, lr2)],
        mercator_project=True,
        origin="upper",
    ).add_to(color_gradient)

    folium.LayerControl().add_to(m)
    m.save(filename)


def compare_mtns_on_map(all_mtns, mn1, mn2, filename):
    def get_marker_color(i):
        if i in mn1 and i in mn2:
            return "green"
        elif i in mn1:
            return "red"
        elif i in mn2:
            return "blue"
        else:
            return "white"

    load_dotenv()
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
    MAPBOX_STYLE_URL = os.getenv("MAPBOX_STYLE_URL")
    lats, lons = zip(*[(i.location.latitude, i.location.longitude) for i in mn1])
    m = folium.Map(
        location=[(sum(lats) / len(lats)), (sum(lons) / len(lons))],
        tiles=MAPBOX_STYLE_URL,
        API_key=MAPBOX_TOKEN,
        zoom_start=12,
        attr="Christian Hein",
    )
    [
        (
            folium.Marker(
                location=(float(i.location.latitude), float(i.location.longitude)),
                popup="%s\n%.4f, %.4f\n%im"
                % (
                    str(i.name),
                    i.location.latitude,
                    i.location.longitude,
                    i.location.elevation,
                ),
                icon=folium.Icon(color=get_marker_color(i), icon="mountain"),
            ).add_to(m)
        )
        for i in all_mtns
    ]
    m.save(filename)
