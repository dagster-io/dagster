"""Pipeline definitions for the simple_lakehouse example.
"""
from simple_lakehouse.assets import daily_temperature_highs_table
from simple_lakehouse.lakehouse_def import simple_lakehouse

computed_assets = [daily_temperature_highs_table]
simple_lakehouse_pipeline = simple_lakehouse.build_pipeline_definition(
    "simple_lakehouse_pipeline",
    computed_assets,
)
