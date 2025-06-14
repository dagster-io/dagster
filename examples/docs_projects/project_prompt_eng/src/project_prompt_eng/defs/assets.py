import json
from datetime import datetime
from typing import Literal

import dagster as dg
from dagster_anthropic import AnthropicResource
from pydantic import BaseModel

from project_prompt_eng.defs.resources import NRELResource

# start_location_prompt
PROMPT_LOCATION = """
Given a location and vehicle, return the latitude (as a decimal, range -90 to 90)
and longitude (as a decimal, range -180 to 180) and fuel type of the vehicle
(enum 'ELEC', 'BD' or 'all').

If the location cannot be found return the status a zero. Electric vehicle map to 'ELEC',
biodiesel to 'BD', anything else should be marked as 'all'.

Return everything as a JSON object.

<example>
Input: I'm at 1600 Pennsylvania Avenue NW, Washington, DC 20500 with a Tesla Model 3

Output:
{{
    'latitude': 38.8977,
    'longitude': -77.0365,
    'fuel_type': 'ELEC',
}}
</example>

Input: {location}
"""
# end_location_prompt


# start_fuel_station_prompt
PROMPT_FUEL_STATION_OPEN = """
Given the hours of operation ('hours_of_operation': str) and and timestamp ('datetime': str).
Determine if the datetime ('%Y-%m-%d %H:%M:%S') falls within the hours of operation.

Only return the answer as a JSON object containing the is_open (as a boolean). No other information.

<example>
Input: {{
    'hours_of_operation': '7am-7pm M-Th and Sat, 7am-8pm F, 9am-5pm Sun', 
    'datetime': '2025-01-21 18:00:00',
}}

Output:
{{
    'is_open': True,
}}
</example>

<example>
Input: {{
    'hours_of_operation': '7am-7pm M-Th and Sat, 7am-8pm F, 9am-5pm Sun', 
    'datetime': '2025-01-21 6:00:00',
}}

Output:
{{
    'is_open': False,
}}
</example>

Input: {fuel_station_hours}
"""
# end_fuel_station_prompt


# start_user_input_prompt
class UserInputSchema(BaseModel):
    latitude: float
    longitude: float
    fuel_type: Literal["all", "ELEC", "BD"]


class InputLocation(dg.Config):
    location: str


@dg.asset(
    kinds={"anthropic"},
    description="Determine location and vehicle type from an input",
)
def user_input_prompt(
    context: dg.AssetExecutionContext,
    config: InputLocation,
    anthropic: AnthropicResource,
) -> UserInputSchema:
    prompt = PROMPT_LOCATION.format(location=config.location)

    with anthropic.get_client(context) as client:
        resp = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )

    message = resp.content[0].text
    schema = UserInputSchema(**json.loads(message))
    context.log.info(schema)
    return schema


# end_user_input_prompt


# start_nearest_fuel_stations
@dg.asset(
    kinds={"python"},
    description="Find the nearest alt fuel stations",
)
def nearest_fuel_stations(nrel: NRELResource, user_input_prompt: UserInputSchema) -> list[dict]:
    fuel_stations = nrel.alt_fuel_stations(
        latitude=user_input_prompt.latitude,
        longitude=user_input_prompt.longitude,
        fuel_type=user_input_prompt.fuel_type,
    )
    nearest_stations_with_hours = []
    for fuel_station in fuel_stations:
        if fuel_station.get("access_days_time"):
            nearest_stations_with_hours.append(fuel_station)
            if len(nearest_stations_with_hours) == 3:
                break
    return nearest_stations_with_hours


# end_nearest_fuel_stations


# start_available_fuel_stations
@dg.asset(
    kinds={"anthropic"},
    description="Determine if the nearest stations are available",
)
def available_fuel_stations(
    context: dg.AssetExecutionContext,
    anthropic: AnthropicResource,
    nearest_fuel_stations,
):
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    fuel_stations_open = 0
    with anthropic.get_client(context) as client:
        for fuel_station in nearest_fuel_stations:
            prompt_input = {
                "access_days_time": fuel_station["access_days_time"],
                "datetime": current_time,
            }

            prompt = PROMPT_FUEL_STATION_OPEN.format(fuel_station_hours=prompt_input)
            resp = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}],
            )

            message = resp.content[0].text
            data = json.loads(message)

            if data["is_open"]:
                context.log.info(
                    f"{fuel_station['station_name']} at {fuel_station['street_address']} is {fuel_station['distance']} miles away"
                )
                fuel_stations_open += 1

    if fuel_stations_open == 0:
        context.log.info("Sorry, no available fuel stations right now")


# end_available_fuel_stations
