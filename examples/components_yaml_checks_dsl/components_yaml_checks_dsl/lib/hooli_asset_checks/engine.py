from datetime import datetime
from typing import Optional

import dagster as dg
import pandas as pd


def evaluate_static_threshold(
    latest_value: float, min_value: Optional[float] = None, max_value: Optional[float] = None
) -> dg.AssetCheckResult:
    passed = True

    latest_value_metadata = None

    if isinstance(latest_value, datetime):
        latest_value_metadata = dg.MetadataValue.timestamp(latest_value)
    else:
        latest_value_metadata = float(latest_value)  # For numeric consistency

    if isinstance(latest_value_metadata, pd.Timestamp):
        latest_value_metadata = latest_value_metadata.to_pydatetime()

    if isinstance(min_value, str):
        min_value_metadata = datetime.fromisoformat(min_value)
    else:
        min_value_metadata = min_value

    if isinstance(max_value, str):
        max_value_metadata = datetime.fromisoformat(max_value)
    else:
        max_value_metadata = max_value

    if min_value is not None and latest_value < min_value:
        passed = False
    if max_value is not None and latest_value > max_value:
        passed = False

    return dg.AssetCheckResult(
        passed=passed,
        metadata={
            "min_threshold": min_value_metadata,
            "max_threshold": max_value_metadata,
            "latest": latest_value_metadata,
        },
    )
