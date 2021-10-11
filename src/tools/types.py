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
