import requests

import dagster as dg


class SunResource(dg.ConfigurableResource):
    latitude: str
    longitude: str
    time_zone: str

    @property
    def query_string(self) -> str:
        return f"https://api.sunrise-sunset.org/json?lat={self.latitude}&lng={self.longitude}&date=today&tzid={self.time_zone}"

    def sunrise(self) -> str:
        data = requests.get(self.query_string, timeout=5).json()
        return data["results"]["sunrise"]


# highlight-start
# Define the home_sunrise asset and use the sun_resource
@dg.asset
def home_sunrise(context: dg.AssetExecutionContext, sun_resource: SunResource) -> None:
    sunrise = sun_resource.sunrise()
    context.log.info(f"Sunrise at home is at {sunrise}.")


# highlight-end

defs = dg.Definitions(
    assets=[home_sunrise],
    # highlight-start
    # Update the configuration to use environment variables
    resources={
        "sun_resource": SunResource(
            latitude=dg.EnvVar("HOME_LATITUDE"),
            longitude=dg.EnvVar("HOME_LONGITUDE"),
            time_zone=dg.EnvVar("HOME_TIMEZONE"),
        )
    },
    # highlight-end
)
