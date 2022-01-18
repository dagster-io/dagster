from dagster import repository
from software_defined_assets.spark_weather_job import spark_weather_job


@repository
def software_defined_assets():
    return [spark_weather_job]
