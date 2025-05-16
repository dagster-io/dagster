import dagster as dg
import requests
from dagster_anthropic import AnthropicResource
from pydantic import Field

BASE_URL = "https://developer.nrel.gov/api/alt-fuel-stations/v1.json"


# start_resource
class NRELResource(dg.ConfigurableResource):
    api_key: str = Field(description=("NREL API key. See https://developer.nrel.gov/signup/"))

    def alt_fuel_stations(self, latitude: float, longitude: float, fuel_type: str = "all"):
        if fuel_type not in {"BD", "ELEC", "all"}:
            raise ValueError(f"{fuel_type} is not a valid fuel type")

        url = "https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json"

        params = {
            "api_key": self.api_key,
            "latitude": latitude,
            "longitude": longitude,
            "radius": 5.0,
            "fuel_type": fuel_type,
            "status": "E",
        }

        resp = requests.get(url, params=params)
        return resp.json()["fuel_stations"]


# end_resource


defs = dg.Definitions(
    resources={
        "nrel": NRELResource(api_key=dg.EnvVar("NREL_API_KEY")),
        "anthropic": AnthropicResource(api_key=dg.EnvVar("ANTHROPIC_API_KEY")),
    },
)
