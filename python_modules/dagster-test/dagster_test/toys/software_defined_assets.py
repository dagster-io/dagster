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
    """Computes the temperature high for each day."""
    assert sfo_q2_weather_sample
    time.sleep(3)
    return DataFrame()


@asset
def hottest_dates(daily_temperature_highs: DataFrame) -> DataFrame:
    """Computes the 10 hottest dates.

    In a more advanced demo, this might perform a complex SQL query to aggregate the data. For now,
    just imagine that this implements something like:

    ```sql
    SELECT temp, date_part('day', date) FROM daily_temperature_highs ORDER BY date DESC;
    ```

    This could make use of [DATE_PART](https://www.postgresql.org/docs/8.1/functions-datetime.html),
    and we can even link to that because this supports Markdown.

    This concludes the demo of a long asset description.
    """
    assert daily_temperature_highs
    time.sleep(3)
    return DataFrame()


software_defined_assets = AssetGroup(
    assets=[daily_temperature_highs, hottest_dates],
    source_assets=[sfo_q2_weather_sample],
    resource_defs={"io_manager": IOManagerDefinition.hardcoded_io_manager(DummyIOManager())},
)
