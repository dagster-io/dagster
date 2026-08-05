from dagster import repository

from .core_trip import core_trip  # ty: ignore[unresolved-import]
from .custom_column_constraint import (
    custom_column_constraint_trip,  # ty: ignore[unresolved-import]
)
from .shape_constrained_trip import (
    shape_constrained_trip,  # ty: ignore[unresolved-import]
)
from .summary_stats import summary_stats_trip  # ty: ignore[unresolved-import]


@repository
def dagster_pandas_guide_examples():
    return {
        "jobs": {
            "custom_column_constraint_trip": lambda: custom_column_constraint_trip,
            "shape_constrained_trip": lambda: shape_constrained_trip,
            "summary_stats_trip": lambda: summary_stats_trip,
            "core_trip": lambda: core_trip,
        }
    }
