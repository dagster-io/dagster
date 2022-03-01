from software_defined_assets.spark_weather_job import spark_weather_job

from dagster import repository


@repository
def software_defined_assets():
    return [spark_weather_job]
