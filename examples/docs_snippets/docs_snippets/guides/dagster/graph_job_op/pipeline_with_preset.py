from dagster import PresetDefinition, 

from dagster.legacy import pipeline
from dagster.legacy import solid


@solid(config_schema={"param": str})
def do_something(_):
    ...


@pipeline(
    preset_defs=[
        PresetDefinition(
            "my_preset",
            run_config={"solids": {"do_something": {"config": {"param": "some_val"}}}},
        )
    ]
)
def do_it_all():
    do_something()
