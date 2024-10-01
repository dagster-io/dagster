from assets_pandas_pyspark.definitions import get_spark_weather_defs, get_weather_defs


def test_weather_defs_can_load():
    assert get_weather_defs()


def test_spark_weather_defs_can_load():
    assert get_spark_weather_defs()
