"""Pipeline definitions for the simple_pyspark example."""
from dagster import ModeDefinition, PresetDefinition, pipeline
from dagster.core.definitions.no_step_launcher import no_step_launcher
from dagster_aws.emr import emr_pyspark_step_launcher
from dagster_aws.s3 import s3_pickle_io_manager, s3_resource
from dagster_databricks import databricks_pyspark_step_launcher
from dagster_pyspark import pyspark_resource

from .solids import (
    make_daily_temperature_high_diffs,
    make_daily_temperature_highs,
    make_weather_samples,
)

local_mode = ModeDefinition(
    name="local",
    resource_defs={"pyspark_step_launcher": no_step_launcher, "pyspark": pyspark_resource},
)


prod_emr_mode = ModeDefinition(
    name="prod_emr",
    resource_defs={
        "pyspark_step_launcher": emr_pyspark_step_launcher,
        "pyspark": pyspark_resource,
        "s3": s3_resource,
        "io_manager": s3_pickle_io_manager,
    },
)


prod_databricks_mode = ModeDefinition(
    name="prod_databricks",
    resource_defs={
        "pyspark_step_launcher": databricks_pyspark_step_launcher,
        "pyspark": pyspark_resource,
        "s3": s3_resource,
        "io_manager": s3_pickle_io_manager,
    },
)


@pipeline(
    mode_defs=[local_mode, prod_emr_mode, prod_databricks_mode],
    preset_defs=[
        PresetDefinition.from_pkg_resources(
            name="local",
            mode="local",
            pkg_resource_defs=[
                ("dagster_examples.simple_pyspark.environments", "local.yaml"),
            ],
        ),
        PresetDefinition.from_pkg_resources(
            name="prod_emr",
            mode="prod_emr",
            pkg_resource_defs=[
                ("dagster_examples.simple_pyspark.environments", "prod_emr.yaml"),
                ("dagster_examples.simple_pyspark.environments", "s3_storage.yaml"),
            ],
        ),
        PresetDefinition.from_pkg_resources(
            name="prod_databricks",
            mode="prod_databricks",
            pkg_resource_defs=[
                ("dagster_examples.simple_pyspark.environments", "prod_databricks.yaml"),
                ("dagster_examples.simple_pyspark.environments", "s3_storage.yaml"),
            ],
        ),
    ],
)
def simple_pyspark_sfo_weather_pipeline():
    """Computes some basic statistics over weather data from SFO airport"""
    make_daily_temperature_high_diffs(make_daily_temperature_highs(make_weather_samples()))


def define_simple_pyspark_sfo_weather_pipeline():
    return simple_pyspark_sfo_weather_pipeline
