import dagster as dg

from resources import NRELResource
from dagster_openai import OpenAIResource


PROMPT = """
Given a location, return the latitude (as a decimal, range -90 to 90)
and longitude (as a decimal, range -180 to 180). If the location
cannot be found return the status a zero. Return everything as a JSON
object.

<example>
Input: I live at 1600 Pennsylvania Avenue NW, Washington, DC 20500

Output:
{
    "Latitude": 38.8977,
    "Longitude": -77.0365,
    "status": 1,
}
</example>

Here is the location: {location}
"""

# https://developer.nrel.gov/docs/transportation/alt-fuel-stations-v1/nearest/


class InputLocation(dg.Config):
    location: str
    limit: int = 3


@dg.asset(
    kinds={"openai"},
)
def location(
    config: InputLocation,
    openai: OpenAIResource,
) -> dict:
    prompt = PROMPT.format(location = config.location)



    if location["status"] == 1:
        return location



@dg.asset(
    kinds={"python"},
)
def nearest_(
    context: dg.AssetCheckExecutionContext,
    nrel: NRELResource,
    location
):
    nrel.alt_fuel_stations(
        latitude=location["latitude"],
        longitude=location["longitude"],
    )

    context.add_output_metadata(
        {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        }
    )