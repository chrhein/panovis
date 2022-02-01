import operator
from dataclasses import dataclass

import location_handler
from pygeodesy.sphericalNvector import LatLon


@dataclass
class Location:
    latitude: float
    longitude: float
    elevation: float = 0.0

    def loc(self):
        return (self.latitude, self.longitude)


# Might delete this later, wasn't use for it
@dataclass
class MountainBounds:
    bounds = ()

    def __init__(self, lat, lon):
        displaced_coordinates = [
            location_handler.displace_camera(lat, lon, deg=i, distance=0.15)
            for i in range(0, 360 + 1, 45)
        ]
        self.bounds = (
            LatLon(*displaced_coordinates[0]),
            LatLon(*displaced_coordinates[1]),
            LatLon(*displaced_coordinates[2]),
            LatLon(*displaced_coordinates[3]),
            LatLon(*displaced_coordinates[4]),
            LatLon(*displaced_coordinates[5]),
            LatLon(*displaced_coordinates[6]),
            LatLon(*displaced_coordinates[7]),
        )

    def get_bounds(self):
        return self.bounds

    def __eq__(self, other):
        return (
            self.min_latitude == other.min_latitude
            and self.max_latitude == other.max_latitude
            and self.min_longitude == other.min_longitude
            and self.max_longitude == other.max_longitude
        )

    def __hash__(self):
        return hash(str(self))

    def __cmp__(self, other):
        return operator.eq((str(self), str(other)))


@dataclass
class Location3D:
    yaw: float
    pitch: float
    distance: float


@dataclass
class Mountain:
    name: str
    location: Location
    bounds: MountainBounds
    location_in_3d: Location3D = None

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(str(self.name))

    def __cmp__(self, other):
        return operator.eq((str(self), str(other)))

    def set_location_in_3d(self, location_in_3d):
        self.location_in_3d = location_in_3d


@dataclass
class ImageInSight:
    name: str
    thumbnail_path: str
    location: Location
    location_in_3d: Location3D = None

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(str(self.name))

    def __cmp__(self, other):
        return operator.eq((str(self), str(other)))

    def set_location_in_3d(self, location_in_3d):
        self.location_in_3d = location_in_3d


@dataclass
class TextureBounds:
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    min_x: float
    min_y: float
    max_x: float
    max_y: float


@dataclass
class Texture:
    dem: str
    texture: str
    camera: Location
    viewpoint: Location
    angle: int
    scale: float
    bounds: TextureBounds


@dataclass(init=False)
class ImageData:
    filename: str
    folder: str
    path: str
    thumbnail_path: str
    render_path: str
    gradient_path: str
    overlay_path: str
    ultrawide_path: str
    hotspots: dict = None
    view_direction: float = None
    fov_l: float = None
    fov_r: float = None

    def __init__(self, path):
        self.path = path
        self.filename = path.split("/")[-1].split(".")[0]
        self.folder = "/".join(path.split("/")[:-1])
        self.render_path = self.path.replace(
            f"{self.filename}.jpg", f"{self.filename}-render.png"
        )
        self.gradient_path = self.path.replace(
            f"{self.filename}.jpg", f"{self.filename}-gradient.png"
        )
        self.overlay_path = self.path.replace(
            f"{self.filename}.jpg", f"{self.filename}-overlay.jpg"
        )
        self.ultrawide_path = self.path.replace(
            f"{self.filename}.jpg", f"{self.filename}-ultrawide.jpg"
        )
        self.thumbnail_path = self.path.replace(
            f"{self.filename}.jpg", f"{self.filename}-thumbnail.jpg"
        )

        self.hotspots = {}
        self.all_images = set()

    def add_hotspots(this, gpx, hotspots):
        print()
        print("Adding hotspots to image data")
        print(f"gpx-file: {gpx}")
        print(hotspots)
        this.hotspots.update({f"{this.filename}-{gpx}": hotspots})
