'''Pipeline definitions for the simple_lakehouse example.
'''
from .assets import daily_temperature_high_diffs_asset, daily_temperature_highs_asset
from .lakehouse import simple_lakehouse

computed_assets = [daily_temperature_highs_asset, daily_temperature_high_diffs_asset]
simple_lakehouse_pipeline = simple_lakehouse.build_pipeline_definition(
    'simple_lakehouse_pipeline', computed_assets,
)
