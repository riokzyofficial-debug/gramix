from __future__ import annotations
from dataclasses import dataclass


@dataclass(slots=True)
class Location:
    longitude: float
    latitude: float
    horizontal_accuracy: float | None = None
    live_period: int | None = None
    heading: int | None = None
    proximity_alert_radius: int | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Location:
        return cls(
            longitude=data["longitude"],
            latitude=data["latitude"],
            horizontal_accuracy=data.get("horizontal_accuracy"),
            live_period=data.get("live_period"),
            heading=data.get("heading"),
            proximity_alert_radius=data.get("proximity_alert_radius"),
        )


@dataclass(slots=True)
class Venue:
    location: Location
    title: str
    address: str
    foursquare_id: str | None = None
    foursquare_type: str | None = None
    google_place_id: str | None = None
    google_place_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict) -> Venue:
        return cls(
            location=Location.from_dict(data["location"]),
            title=data["title"],
            address=data["address"],
            foursquare_id=data.get("foursquare_id"),
            foursquare_type=data.get("foursquare_type"),
            google_place_id=data.get("google_place_id"),
            google_place_type=data.get("google_place_type"),
        )
