import pandas as pd
from dagster import asset


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
