from dagster import Field, InputDefinition, Int, List, configured, pipeline, solid


# start_configured_named
@solid(
    config_schema={
        "is_sample": Field(bool, is_required=False, default_value=False),
    },
    input_defs=[InputDefinition("xs", List[Int])],
)
def get_dataset(context, xs):
    if context.solid_config["is_sample"]:
        return xs[:5]
    else:
        return xs


# If we want to use the same solid configured in multiple ways in the same pipeline,
# we have to specify unique names when configuring them:
sample_dataset = configured(get_dataset, name="sample_dataset")({"is_sample": True})
full_dataset = configured(get_dataset, name="full_dataset")({"is_sample": False})


@pipeline
def dataset_pipeline():
    sample_dataset()
    full_dataset()


# end_configured_named
