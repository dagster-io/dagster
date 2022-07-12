from dagster import PresetDefinition, pipeline, schedule
from dagster.legacy import solid


@solid(config_schema={"param": str})
def do_something(_):
    ...


do_it_all_preset = PresetDefinition(
    "my_preset",
    run_config={"solids": {"do_something": {"config": {"param": "some_val"}}}},
)


@pipeline(preset_defs=[do_it_all_preset])
def do_it_all():
    do_something()


@schedule(cron_schedule="0 0 * * *", pipeline_name="do_it_all")
def do_it_all_schedule():
    return do_it_all_preset.run_config
