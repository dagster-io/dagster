from software_defined_assets.weather_job import weather_job


def test_airport_weather_job():
    assert weather_job.execute_in_process().success
