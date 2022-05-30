import base64
from dotenv import load_dotenv
import folium
import folium.raster_layers
import os
import location_handler
from tools.debug import p_i
from branca.element import Template, MacroElement


def get_glyph(id, color, elevation, min_ele, max_ele):
    scaling = (elevation - min_ele) * 15 / (max_ele - min_ele)
    width = 8 + scaling
    height = 16 + scaling
    glyph = f"""
            <!doctype html>
            <html>
                <head>
                    <style>
                        #triangle-{id} {{
                            width: 0;
                            height: 0;
                            border-left: {width}px solid transparent;
                            border-right: {width}px solid transparent;
                            border-bottom: {height}px solid {color};
                            transform: translate(-{width / 2}px, -{height / 2}px);
                            filter: drop-shadow(2px -3px 4px rgba(255, 255, 255, .33));
                        }}
                    </style>
                </head>
                <body>
                    <div id="triangle-{id}"></div>
                </body>
            </html>"""
    return glyph


def plot_to_map(
    camera_pano_path,
    mountains_in_sight,
    coordinates,
    filename,
    dem_file,
    converter,
    locs=None,
    mountains=None,
    images=None,
):
    p_i("Creating Interactive Map")
    c_lat, c_lon, _, _ = coordinates
    ll, ul, ur, lr = location_handler.get_raster_bounds(dem_file)
    load_dotenv()
    MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN")
    MAPBOX_STYLE_URL = os.getenv("MAPBOX_STYLE_URL")
    m = folium.Map(
        [c_lat, c_lon],
        tiles=None,
        zoom_start=12,
        scrollWheelZoom=False,
    )
    folium.TileLayer(
        location=[c_lat, c_lon],
        tiles=MAPBOX_STYLE_URL,
        API_key=MAPBOX_TOKEN,
        attr="Christian Hein",
        name="Map",
    ).add_to(m)

    min_ele, max_ele = 10000, 0
    for i in mountains:
        if i.location.elevation > max_ele:
            max_ele = i.location.elevation
        if i.location.elevation < min_ele:
            min_ele = i.location.elevation

    ###########################################################################
    ###########################################################################
    # All mountains in dataset

    if mountains:
        mountains_fg = folium.FeatureGroup(name="All Mountains", show=False)
        m.add_child(mountains_fg)
        [
            (
                folium.Marker(
                    location=(i.location.latitude, i.location.longitude),
                    popup="%s\n%im"
                    % (
                        str(i.name),
                        i.location.elevation,
                    ),
                    icon=folium.DivIcon(html=get_glyph(
                        f"am-{i.name}-{int(i.location.elevation)}", "#755239", i.location.elevation, min_ele, max_ele)),
                    zIndexOffset=1,
                ).add_to(mountains_fg)
            )
            for i in mountains
        ]

    ###########################################################################
    ###########################################################################
    # Mountains in sight

    if mountains_in_sight:
        mountains_in_sight_fg = folium.FeatureGroup(
            name="Visible Mountains", show=True)
        m.add_child(mountains_in_sight_fg)

        [
            (
                folium.Marker(
                    location=(i.location.latitude, i.location.longitude),
                    popup="%s\n%im"
                    % (
                        str(i.name),
                        i.location.elevation,
                    ),
                    icon=folium.DivIcon(html=get_glyph(
                        f"vm-{i.name}-{int(i.location.elevation)}", "#426877", i.location.elevation, min_ele, max_ele)),
                    zIndexOffset=10,
                ).add_to(mountains_in_sight_fg)
            )
            for i in mountains_in_sight
        ]

    ###########################################################################
    ###########################################################################
    # Other images in dataset

    if images:
        images_fg = folium.FeatureGroup(name="Visible Images", show=True)
        m.add_child(images_fg)
        for im in images:
            encoded = base64.b64encode(open(im.thumbnail_path, "rb").read())

            html = f'''
            <!doctype html>
            <html>
                <head>
                    <style>
                        .redirect-button {{
                            color: #fff;
                            cursor: pointer;
                            background-color: #6c757d;
                            border-color: #6c757d;
                            display: inline-block;
                            font-weight: 400;
                            line-height: 1.5;
                            text-align: center;
                            text-decoration: none;
                            vertical-align: middle;
                            padding: .375rem .75rem;
                            border-radius: .25rem;
                            transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s ease-in-out,box-shadow .15s ease-in-out;
                        }}

                        .redirect-button:hover {{
                            color: #fff;
                            background-color: #5c636a;
                            border-color: #545b62;
                        }}
                    </style>
                    <script type="text/javascript">
                        function redirect() {{
                            console.log("Redirecting to: ", "{im.name}");
                            window.parent.parent.postMessage("{im.name}", '*');
                        }}
                    </script>
                </head>
                <body>
                    <button class="redirect-button" onclick="redirect();">View image</button>
                    <img src="data:image/JPG;base64,{encoded.decode("UTF-8")}">
                </body>
            </html>
            '''
            iframe = folium.IFrame(
                html, width=450 + 20, height=150 + 20
            )
            popup = folium.Popup(iframe, max_width=470)

            folium.Marker(
                location=(im.location.latitude, im.location.longitude),
                popup=popup,
                icon=folium.Icon(color="orange", icon="camera"),
                zIndexOffset=12,

            ).add_to(images_fg)

    ###########################################################################
    ###########################################################################
    # Current viewpoint

    encoded = base64.b64encode(open(camera_pano_path, "rb").read())
    html = f'''
    <!doctype html>
    <html>
        <img src="data:image/JPG;base64,{encoded.decode("UTF-8")}">
    </html>
    '''
    iframe = folium.IFrame(
        html, width=450 + 20, height=150 + 20
    )
    popup = folium.Popup(iframe, max_width=450)
    folium.Marker(
        location=[c_lat, c_lon],
        popup=popup,
        icon=folium.Icon(color="green", icon="camera"),
        zIndexOffset=13,

    ).add_to(m)

    ###########################################################################
    ###########################################################################
    # Visible coordinates

    if locs:
        locs_fg = folium.FeatureGroup(name="Retrieved Coordinates", show=True)
        m.add_child(locs_fg)
        for i in locs:
            loc = converter.convert(*i)
            folium.Circle(
                location=(loc.latitude, loc.longitude),
                color="#0a6496",
                fill=True,
                fill_color="#0a6496",
                fill_opacity=1,
                radius=15,
            ).add_to(locs_fg)

    ###########################################################################
    ###########################################################################
    # Raster bounds

    raster_bounds = folium.FeatureGroup(name="Raster Bounds", show=False)
    m.add_child(raster_bounds)
    folium.PolyLine(locations=[ll, ul, ur, lr, ll], color="#d63e29", zIndexOffset=15).add_to(
        raster_bounds
    )

    ###########################################################################
    ###########################################################################
    # Legend

    template = """
    {% macro html(this, kwargs) %}

    <!doctype html>
    <html lang="en">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
    <div id='maplegend' class='maplegend'
        style='position: absolute; z-index:9999; border:2px solid grey; background-color:rgba(255, 255, 255, 0.8);
        border-radius:6px; padding: 10px; font-size:14px; right: 20px; bottom: 20px;'>
        <div class='legend-scale'>
            <ul class='legend-labels'>
                <li><span style='background:#71b025;opacity:1.0;'></span>Current Viewpoint</li>
                <li><span style='background:#f69730;opacity:1.0;'></span>Images in dataset</li>
                <li><span style='background:#755239;opacity:1.0;'></span>All mountains in dataset</li>
                <li><span style='background:#426877;opacity:1.0;'></span>Mountains in sight</li>
                <li><span style='background:#d63e29;opacity:1.0;'></span>DEM bounding box</li>
            </ul>
        </div>
    </div>
    </body>
    </html>

    <style type='text/css'>
    .maplegend .legend-title {
        text-align: left;
        margin-bottom: 5px;
        font-weight: bold;
        font-size: 90%;
        }
    .maplegend .legend-scale ul {
        margin: 0;
        margin-bottom: 5px;
        padding: 0;
        float: left;
        list-style: none;
        }
    .maplegend .legend-scale ul li {
        font-size: 80%;
        list-style: none;
        margin-left: 0;
        line-height: 18px;
        margin-bottom: 2px;
        }
    .maplegend ul.legend-labels li span {
        display: block;
        float: left;
        height: 16px;
        width: 30px;
        margin-right: 5px;
        margin-left: 0;
        border: 1px solid #999;
        }
    .maplegend .legend-source {
        font-size: 80%;
        color: #777;
        clear: both;
        }
    .maplegend a {
        color: #777;
        }
    </style>
    {% endmacro %}"""

    macro = MacroElement()
    macro._template = Template(template)

    ###########################################################################
    ###########################################################################
    # Add to map
    folium.LayerControl().add_to(m)
    m.get_root().add_child(macro)
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
    lats, lons = zip(*[(i.location.latitude, i.location.longitude)
                     for i in mn1])
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
                location=(float(i.location.latitude),
                          float(i.location.longitude)),
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
