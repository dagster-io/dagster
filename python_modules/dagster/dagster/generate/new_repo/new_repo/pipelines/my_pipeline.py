from dagster import ModeDefinition, pipeline

from ..solids import hello

# Mode definitions allow you to configure the behavior of your pipelines and solids at execution
# time. For hints on creating modes in Dagster, see our documentation overview on Modes and
# Resources: https://docs.dagster.io/overview/modes-resources-presets/modes-resources
MODE_DEV = ModeDefinition(name="dev", resource_defs={})
MODE_TEST = ModeDefinition(name="test", resource_defs={})


@pipeline(mode_defs=[MODE_DEV, MODE_TEST])
def my_pipeline():
    """
    A pipeline definition. This example pipeline has a single solid.

    For more hints on writing Dagster pipelines, see our documentation overview on Pipelines:
    https://docs.dagster.io/overview/solids-pipelines/pipelines
    """
    hello()
