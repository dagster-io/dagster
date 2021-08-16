# pylint: disable=unused-argument

from dagster import (
    DependencyDefinition,
    ModeDefinition,
    PipelineDefinition,
    PresetDefinition,
    execute_pipeline,
    pipeline,
    solid,
)


@solid
def my_solid():
    pass


# start_pipeline_example_marker
@solid
def return_one(context):
    return 1


@solid
def add_one(context, number: int):
    return number + 1


@pipeline
def one_plus_one_pipeline():
    add_one(return_one())


# end_pipeline_example_marker

# start_multiple_usage_pipeline
@pipeline
def multiple_usage_pipeline():
    add_one(add_one(return_one()))


# end_multiple_usage_pipeline

# start_alias_pipeline
@pipeline
def alias_pipeline():
    add_one.alias("second_addition")(add_one(return_one()))


# end_alias_pipeline


# start_tag_pipeline
@pipeline
def tag_pipeline():
    add_one.tag({"my_tag": "my_value"})(add_one(return_one()))


# end_tag_pipeline


# start_pipeline_definition_marker
one_plus_one_pipeline_def = PipelineDefinition(
    name="one_plus_one_pipeline",
    solid_defs=[return_one, add_one],
    dependencies={"add_one": {"number": DependencyDefinition("return_one")}},
)
# end_pipeline_definition_marker


# start_modes_pipeline
dev_mode = ModeDefinition("dev")
staging_mode = ModeDefinition("staging")
prod_mode = ModeDefinition("prod")


@pipeline(mode_defs=[dev_mode, staging_mode, prod_mode])
def my_modes_pipeline():
    my_solid()


# end_modes_pipeline

# start_preset_pipeline
@pipeline(
    preset_defs=[
        PresetDefinition(
            name="one",
            run_config={"solids": {"add_one": {"inputs": {"number": 1}}}},
        ),
        PresetDefinition(
            name="two",
            run_config={"solids": {"add_one": {"inputs": {"number": 2}}}},
        ),
    ]
)
def my_presets_pipeline():
    add_one()


# end_preset_pipeline

# start_run_preset


def run_pipeline():
    execute_pipeline(my_presets_pipeline, preset="one")


# end_run_preset


# start_tags_pipeline
@pipeline(tags={"my_tag": "my_value"})
def my_tags_pipeline():
    my_solid()


# end_tags_pipeline
