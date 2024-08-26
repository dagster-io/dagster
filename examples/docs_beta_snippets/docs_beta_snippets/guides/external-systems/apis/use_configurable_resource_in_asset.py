import requests

import dagster as dg


class SunResource(dg.ConfigurableResource):
    latitude: float
    longitude: float
    time_zone: str

    @property
    def query_string(self) -> str:
        return f"https://api.sunrise-sunset.org/json?lat={self.latitude}&lng={self.longitude}&date=today&tzid={self.time_zone}"

    def sunrise(self) -> str:
        data = requests.get(self.query_string, timeout=5).json()
        return data["results"]["sunrise"]


# highlight-start
@dg.asset
def sfo_sunrise(context: dg.AssetExecutionContext, sun_resource: SunResource) -> None:
    sunrise = sun_resource.sunrise()
    context.log.info(f"Sunrise in San Francisco is at {sunrise}.")


defs = dg.Definitions(
    assets=[sfo_sunrise],
    resources={
        "sun_resource": SunResource(
            latitude=37.615223, longitude=-122.389977, time_zone="America/Los_Angeles"
        )
    },
)

# highlight-end
