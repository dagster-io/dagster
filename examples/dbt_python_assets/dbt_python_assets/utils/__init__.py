import datetime
import time
import uuid
from typing import Any, Dict, List

import numpy as np
import pandas as pd


def _random_times(n: int):
    """Generate some random times that generally become more frequent as time goes on."""
    time.sleep(0.5)
    start = pd.to_datetime("2022-01-01")
    end = pd.to_datetime(datetime.datetime.now())

    start_u = start.value // 10**9
    end_u = end.value // 10**9

    dist = np.random.standard_exponential(size=n) / 10

    clipped_flipped_dist = 1 - dist[dist <= 1]
    clipped_flipped_dist = clipped_flipped_dist[:-1]

    if len(clipped_flipped_dist) < n:
        clipped_flipped_dist = np.append(
            clipped_flipped_dist, clipped_flipped_dist[: n - len(clipped_flipped_dist)]
        )

    return pd.to_datetime((clipped_flipped_dist * (end_u - start_u)) + start_u, unit="s")


def random_data(extra_columns: Dict[str, Any], n: int) -> pd.DataFrame:
    # always have user_id and day
    data = {"user_id": np.random.randint(0, 1000, size=n), "dt": _random_times(n)}
    for name, dtype in extra_columns.items():
        if dtype == str:
            data[name] = [uuid.uuid4() for _ in range(n)]
        elif dtype == int:
            data[name] = np.random.randint(0, 100, size=n)
        elif dtype == float:
            data[name] = 100 * np.random.random(size=n)
    return pd.DataFrame(data)
