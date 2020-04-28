'''Pipeline definitions for the simple_pyspark example.
'''
from dagster_pyspark import pyspark_resource

from dagster import ModeDefinition, PresetDefinition, pipeline

from .solids import (
    make_daily_temperature_high_diffs,
    make_daily_temperature_highs,
    make_weather_samples,
)

local_mode = ModeDefinition(name='local', resource_defs={'pyspark': pyspark_resource,},)


@pipeline(
    mode_defs=[local_mode],
    preset_defs=[
        PresetDefinition.from_pkg_resources(
            name='local',
            mode='local',
            pkg_resource_defs=[
                ('dagster_examples.simple_pyspark.environments', 'local.yaml'),
                ('dagster_examples.simple_pyspark.environments', 'filesystem_storage.yaml'),
            ],
        ),
    ],
)
def simple_pyspark_sfo_weather_pipeline():
    '''Computes some basic statistics over weather data from SFO airport'''
    make_daily_temperature_high_diffs(make_daily_temperature_highs(make_weather_samples()),)


def define_simple_pyspark_sfo_weather_pipeline():
    return simple_pyspark_sfo_weather_pipeline
