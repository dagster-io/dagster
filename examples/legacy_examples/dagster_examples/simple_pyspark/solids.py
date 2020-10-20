"""Solid definitions for the simple_pyspark example."""

import dagster_pyspark
from dagster import make_python_type_usable_as_dagster_type, solid
from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as f

# Make pyspark.sql.DataFrame map to dagster_pyspark.DataFrame
make_python_type_usable_as_dagster_type(
    python_type=DataFrame, dagster_type=dagster_pyspark.DataFrame
)


@solid(required_resource_keys={"pyspark_step_launcher", "pyspark"})
def make_weather_samples(context, file_path: str) -> DataFrame:
    """Loads the weather data from a CSV"""
    return (
        context.resources.pyspark.spark_session.read.format("csv")
        .options(header="true")
        .load(file_path)
    )


@solid(required_resource_keys={"pyspark_step_launcher"})
def make_daily_temperature_highs(_, weather_samples: DataFrame) -> DataFrame:
    """Computes the temperature high for each day"""
    valid_date = f.to_date(weather_samples["valid"]).alias("valid_date")
    return weather_samples.groupBy(valid_date).agg(f.max("tmpf").alias("max_tmpf"))


@solid(required_resource_keys={"pyspark_step_launcher"})
def make_daily_temperature_high_diffs(_, daily_temperature_highs: DataFrame) -> DataFrame:
    """Computes the difference between each day's high and the previous day's high"""
    window = Window.orderBy("valid_date")
    return daily_temperature_highs.select(
        "valid_date",
        (
            daily_temperature_highs["max_tmpf"]
            - f.lag(daily_temperature_highs["max_tmpf"]).over(window)
        ).alias("day_high_diff"),
    )
