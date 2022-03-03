import random

import numpy as np
import pandas as pd
from dagster_postgres.utils import get_conn_string

START_DATE = pd.to_datetime("2021-01-01")
END_DATE = pd.to_datetime("2022-01-01")

N_USERS = 100
N_ORDERS = 10000


def random_dates(start, end):

    start_u = start.value // 10**9
    end_u = end.value // 10**9

    dist = np.random.standard_exponential(size=N_ORDERS) / 10

    clipped_flipped_dist = 1 - dist[dist <= 1]

    return pd.to_datetime((clipped_flipped_dist * (end_u - start_u)) + start_u, unit="s")


con_string = get_conn_string(
    username="postgres", password="password", hostname="localhost", db_name="postgres"
)

users = pd.DataFrame(
    {"user_id": range(N_USERS), "is_bot": [random.choice([True, False]) for _ in range(N_USERS)]}
)

users.to_sql("users", con=con_string, if_exists="replace")

orders = pd.DataFrame(
    {
        "user_id": [random.randint(0, N_USERS) for _ in range(N_ORDERS)],
        "order_time": random_dates(START_DATE, END_DATE),
        "order_value": np.random.normal(loc=100.0, scale=15.0, size=N_ORDERS),
    }
)

orders.to_sql("orders", con=con_string, if_exists="replace")
