import requests

import dagster as dg


class SunResource(dg.ConfigurableResource):
    @property
    def query_string(self) -> str:
        latittude = "37.615223"
        longitude = "-122.389977"
        time_zone = "America/Los_Angeles"
        return f"https://api.sunrise-sunset.org/json?lat={latittude}&lng={longitude}&date=today&tzid={time_zone}"

    def sunrise(self) -> str:
        data = requests.get(self.query_string, timeout=5).json()
        return data["results"]["sunrise"]


# highlight-start
@dg.asset
def sfo_sunrise(context: dg.AssetExecutionContext, sun_resource: SunResource) -> None:
    sunrise = sun_resource.sunrise()
    context.log.info(f"Sunrise in San Francisco is at {sunrise}.")


defs = dg.Definitions(assets=[sfo_sunrise], resources={"sun_resource": SunResource()})

# highlight-end
