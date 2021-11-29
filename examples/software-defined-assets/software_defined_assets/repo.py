from dagster import repository
from software_defined_assets.spark_weather_job import spark_weather_job
from software_defined_assets.weather_job import weather_job


@repository
def software_defined_assets():
    return [weather_job, spark_weather_job]
