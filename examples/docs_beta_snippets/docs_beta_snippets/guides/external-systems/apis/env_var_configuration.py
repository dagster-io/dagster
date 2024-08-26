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
def home_sunrise(context: dg.AssetExecutionContext, sun_resource: SunResource) -> None:
    sunrise = sun_resource.sunrise()
    context.log.info(f"Sunrise at home is at {sunrise}.")


defs = dg.Definitions(
    assets=[home_sunrise],
    resources={
        "sun_resource": SunResource(
            latitude=float(dg.EnvVar("HOME_LATITUDE")),
            longitude=float(dg.EnvVar("HOME_LONGITUDE")),
            time_zone=dg.EnvVar("HOME_TIMEZONE"),
        )
    },
)

# highlight-end
