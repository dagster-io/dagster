from assets_pandas_pyspark.assets.spark_weather_assets import spark_weather_assets

from dagster import Definitions

defs = Definitions(assets=spark_weather_assets)
