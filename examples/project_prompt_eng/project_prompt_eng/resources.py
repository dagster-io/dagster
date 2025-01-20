import dagster as dg
import requests
from pydantic import Field

BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"


class NRELResource(dg.ConfigurableResource):
    api_key: str = Field(
        description=(
            "NREL API key. See https://developer.nrel.gov/signup/"
        )
    )

    def alt_fuel_stations(self, latitude: float, longitude: float):
        url = "https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json"

        params = {
            "api_key": self.api_key,
            "latitude": latitude,
            "longitude": longitude
        }

        return requests.get(url, params=params)
