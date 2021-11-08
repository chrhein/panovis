import operator
from dataclasses import dataclass


@dataclass
class Location:
    latitude: float
    longitude: float
    elevation: float = 0.0


@dataclass
class Mountain:
    name: str
    location: Location

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(str(self.name))

    def __cmp__(self, other):
        return operator.eq((str(self), str(other)))


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
