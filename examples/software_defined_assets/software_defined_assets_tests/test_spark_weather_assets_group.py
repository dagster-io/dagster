from software_defined_assets.spark_weather_assets_group import spark_weather_assets


def test_airport_weather_assets():
    assert spark_weather_assets.build_job(name="job").execute_in_process().success
