from simple_lakehouse.airport_weather_job import airport_weather_job


def test_airport_weather_job():
    assert airport_weather_job.execute_in_process().success
