from dagster import repository

from .core_trip import core_trip
from .custom_column_constraint import custom_column_constraint_trip
from .shape_constrained_trip import shape_constrained_trip
from .summary_stats import summary_stats_trip


@repository
def dagster_pandas_guide_examples():
    return {
        "pipelines": {
            "custom_column_constraint_trip": lambda: custom_column_constraint_trip,
            "shape_constrained_trip": lambda: shape_constrained_trip,
            "summary_stats_trip": lambda: summary_stats_trip,
            "core_trip": lambda: core_trip,
        }
    }
