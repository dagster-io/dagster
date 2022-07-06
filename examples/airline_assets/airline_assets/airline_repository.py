import pandas as pd

from dagster import (
    AssetSelection,
    AssetsDefinition,
    GraphOut,
    asset,
    define_asset_job,
    graph,
    op,
    repository,
)


@asset
def passenger_flights():
    return pd.DataFrame(
        {
            "name": ["Harry Potter", "Ron Weasley", "Hermione Granger"],
            "date": ["2022-07-01", "2022-07-01", "2022-07-01"],
            "departure_city": ["San Francisco", "Los Angeles", "New York"],
            "departure_state": ["CA", "CA", "NY"],
            "departure_country": ["USA", "USA", "USA"],
            "arrival_city": ["San Francisco", "Los Angeles", "New York"],
            "arrival_state": ["CA", "CA", "NY"],
            "arrival_country": ["USA", "USA", "USA"],
            "age": [20, 21, 39],
            "rebooked_due_to_cancellation": [False, False, False],
            "num_layovers": [0, 1, 2],
            "distance_in_miles": [100, 200, 300],
        }
    )


@op
def get_us_flights(passenger_flights):
    # Filter for flights beginning and ending in the US
    us_flights = passenger_flights[
        (passenger_flights["departure_country"] == "USA")
        & (passenger_flights["arrival_country"] == "USA")
    ]

    # Filter out flights that were rebooked due to cancellations
    us_flights = us_flights[us_flights["rebooked_due_to_cancellation"] == False]
    return us_flights


@op
def layover_percentage_breakdown(flights):
    # Group by number of layovers
    grouped_by_num_layovers = flights.groupby("num_layovers").size()
    layover_counts_percentage = grouped_by_num_layovers / len(flights)
    return layover_counts_percentage


@graph(out={"us_flights": GraphOut(), "us_layover_percentages": GraphOut()})
def us_assets(passenger_flights):
    us_flights = get_us_flights(passenger_flights)
    us_layover_percentages = layover_percentage_breakdown(us_flights)
    return {"us_flights": us_flights, "us_layover_percentages": us_layover_percentages}


@op
def filter_for_2022(flights):
    flights["date"] = pd.to_datetime(flights["date"], format="%Y-%m-%d")
    return flights[flights["date"].dt.strftime("%Y") == "2022"]


@graph
def layover_breakdown_2022(us_flights):
    return layover_percentage_breakdown(filter_for_2022(us_flights))


airline_job = define_asset_job("airline_job", AssetSelection.keys("passenger_flights").downstream())


@repository
def airline_repository():
    return [
        define_asset_job("airline_job", AssetSelection.keys("passenger_flights").downstream()),
        passenger_flights,
        AssetsDefinition.from_graph(us_assets),
        AssetsDefinition.from_graph(layover_breakdown_2022),
    ]
