from software_defined_assets.spark_weather_job import spark_weather_job


def test_airport_weather_job():
    assert spark_weather_job.execute_in_process().success
