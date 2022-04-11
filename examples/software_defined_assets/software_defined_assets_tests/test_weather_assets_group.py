from software_defined_assets.weather_assets_group import weather_assets


def test_airport_weather_assets():
    assert weather_assets.build_job(name="job").execute_in_process().success
