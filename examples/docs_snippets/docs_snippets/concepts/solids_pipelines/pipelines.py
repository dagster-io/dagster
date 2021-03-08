# pylint: disable=unused-argument

from dagster import (
    DependencyDefinition,
    InputDefinition,
    ModeDefinition,
    PipelineDefinition,
    pipeline,
    solid,
)


@solid
def my_solid(_):
    pass


# start_pipeline_example_marker
@solid
def return_one(context):
    return 1


@solid(input_defs=[InputDefinition("number", int)])
def add_one(context, number):
    return number + 1


@pipeline
def one_plus_one_pipeline():
    add_one(return_one())


# end_pipeline_example_marker

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

# start_tags_pipeline
@pipeline(tags={"my_tag": "my_value"})
def my_tags_pipeline():
    my_solid()


# end_tags_pipeline
