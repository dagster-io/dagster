from dagster import Field, execute_pipeline, pipeline, solid


@solid(
    config_schema={
        # can just use the expected type as short hand
        "iterations": int,
        # otherwise use Field for optionality, defaults, and descriptions
        "word": Field(str, is_required=False, default_value="hello"),
    }
)
def config_example_solid(context):
    for _ in range(context.solid_config["iterations"]):
        context.log.info(context.solid_config["word"])


@pipeline
def config_example_pipeline():
    config_example_solid()


def run_bad_example():
    # This run will fail to start since there is required config not provided
    return execute_pipeline(config_example_pipeline, run_config={})


def run_other_bad_example():
    # This will also fail to start since iterations is the wrong type
    execute_pipeline(
        config_example_pipeline,
        run_config={"solids": {"config_example_solid": {"config": {"iterations": "banana"}}}},
    )


def run_good_example():
    return execute_pipeline(
        config_example_pipeline,
        run_config={"solids": {"config_example_solid": {"config": {"iterations": 1}}}},
    )
