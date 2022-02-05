import operator
from dataclasses import dataclass
import numpy as np
from osgeo import ogr, osr
from geopy import distance
import numpy as np


@dataclass
class Location:
    latitude: float
    longitude: float
    elevation: float = 0.0

    def loc(self):
        return (self.latitude, self.longitude)


@dataclass
class Location3D:
    yaw: float
    pitch: float
    distance: float


@dataclass
class Location2D:
    x: float
    y: float


@dataclass
class Mountain:
    name: str
    location: Location
    location2d: any
    location_in_3d: Location3D = None
    link: str = None

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(str(self.name))

    def __cmp__(self, other):
        return operator.eq((str(self), str(other)))

    def set_location_in_3d(self, location_in_3d):
        self.location_in_3d = location_in_3d


@dataclass
class Hike:
    name: str
    locations: list


@dataclass
class ImageInSight:
    name: str
    thumbnail_path: str
    location: Location
    location2d: any
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
        fn = f"{this.filename}-{gpx}"
        this.hotspots[fn] = hotspots


@dataclass(init=False)
class CrsToLatLng:
    crs: any
    in_sr: any
    out_sr: any
    transform: any
    latlng_epsg: int = 4326  # WGS84

    def __init__(self, crs):
        self.crs = crs
        self.in_sr = osr.SpatialReference()
        self.out_sr = osr.SpatialReference()
        self.in_sr.ImportFromEPSG(crs)
        self.out_sr.ImportFromEPSG(self.latlng_epsg)
        self.transform = osr.CoordinateTransformation(self.in_sr, self.out_sr)

    def convert(self, lat, lon, ele=0):
        point = ogr.CreateGeometryFromWkt(f"POINT ({lat} {lon})")
        point.Transform(self.transform)
        return Location(
            latitude=float(point.GetX()), longitude=float(point.GetY()), elevation=ele
        )


@dataclass(init=False)
class LatLngToCrs:
    crs: any
    in_sr: any
    out_sr: any
    transform: any
    latlng_epsg: int = 4326  # WGS84

    def __init__(self, crs):
        self.crs = crs
        self.in_sr = osr.SpatialReference()
        self.out_sr = osr.SpatialReference()
        self.in_sr.ImportFromEPSG(self.latlng_epsg)
        self.out_sr.ImportFromEPSG(crs)
        self.transform = osr.CoordinateTransformation(self.in_sr, self.out_sr)

    def convert(self, lat, lon, ele=0):
        point = ogr.CreateGeometryFromWkt(f"POINT ({lat} {lon})")
        point.Transform(self.transform)
        return point


@dataclass
class Distance:
    generator: any = distance

    def get_distance_between_locations(self, loc1, loc2):
        return self.generator.great_circle(
            (loc1.latitude, loc1.longitude), (loc2.latitude, loc2.longitude)
        ).m
