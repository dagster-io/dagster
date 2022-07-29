# pylint: disable=redefined-outer-name
import time

from dagster import AssetKey, IOManager, IOManagerDefinition, SourceAsset, asset
from dagster._legacy import AssetGroup

sfo_q2_weather_sample = SourceAsset(key=AssetKey("sfo_q2_weather_sample"))


class DataFrame:
    pass


class DummyIOManager(IOManager):
    def handle_output(self, context, obj: DataFrame):
        assert context
        assert obj

    def load_input(self, context):
        assert context
        return DataFrame()


@asset
def daily_temperature_highs(sfo_q2_weather_sample: DataFrame) -> DataFrame:
    """Computes the temperature high for each day"""
    assert sfo_q2_weather_sample
    time.sleep(3)
    return DataFrame()


@asset
def hottest_dates(daily_temperature_highs: DataFrame) -> DataFrame:
    """Computes the 10 hottest dates"""
    assert daily_temperature_highs
    time.sleep(3)
    return DataFrame()


software_defined_assets = AssetGroup(
    assets=[daily_temperature_highs, hottest_dates],
    source_assets=[sfo_q2_weather_sample],
    resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(DummyIOManager())},
)
