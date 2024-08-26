import requests

import dagster as dg


class SFOSunResource(dg.ConfigurableResource):
    @property
    def query_string(self) -> str:
        latittude = 37.615223
        longitude = -122.389977
        tzone = "America/Los_Angeles"
        return f"https://api.sunrise-sunset.org/json?lat={latittude}&lng={longitude}&date=today&tzid={tzone}"

    def sunrise(self) -> str:
        data = requests.get(self.query_string, timeout=5).json()
        return data["results"]["sunrise"]
