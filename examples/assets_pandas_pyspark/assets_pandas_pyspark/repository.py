from assets_pandas_pyspark.assets.spark_weather_assets import spark_weather_assets

from dagster import repository


@repository
def assets_pandas_pyspark():
    return [spark_weather_assets]
