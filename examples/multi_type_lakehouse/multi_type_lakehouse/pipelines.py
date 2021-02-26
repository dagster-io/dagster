"""Pipeline definitions for the multi_type_lakehouse example.
"""
from multi_type_lakehouse.assets import (
    daily_temperature_high_diffs_table,
    daily_temperature_highs_table,
)
from multi_type_lakehouse.lakehouse_def import multi_type_lakehouse

computed_assets = [daily_temperature_highs_table, daily_temperature_high_diffs_table]
multi_type_lakehouse_pipeline = multi_type_lakehouse.build_pipeline_definition(
    "multi_type_lakehouse_pipeline",
    computed_assets,
)
