from dagster import repository

from .core_trip_pipeline import trip_pipeline
from .custom_column_constraint_pipeline import custom_column_constraint_pipeline
from .shape_constrained_pipeline import shape_constrained_pipeline
from .summary_stats_pipeline import summary_stats_pipeline


@repository
def dagster_pandas_guide_examples():
    return {
        "pipelines": {
            "custom_column_constraint_pipeline": lambda: custom_column_constraint_pipeline,
            "shape_constrained_pipeline": lambda: shape_constrained_pipeline,
            "summary_stats_pipeline": lambda: summary_stats_pipeline,
            "trip_pipeline": lambda: trip_pipeline,
        }
    }
