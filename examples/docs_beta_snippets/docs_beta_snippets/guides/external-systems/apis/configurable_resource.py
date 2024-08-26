import requests

import dagster as dg


class SunResource(dg.ConfigurableResource):
    latitude: str
    longitude: str
    time_zone: str

    @property
    def query_string(self) -> str:
        return f"https://api.sunrise-sunset.org/json?lat={self.latittude}&lng={self.longitude}&date=today&tzid={self.time_zone}"

    def sunrise(self) -> str:
        data = requests.get(self.query_string, timeout=5).json()
        return data["results"]["sunrise"]
