from software_defined_assets.spark_weather_job import weather_job


def test_airport_weather_job():
    assert weather_job.execute_in_process().success
