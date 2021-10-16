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
