from dagster import InputDefinition, String, execute_pipeline, pipeline, solid


# def_start_marker
@solid(input_defs=[InputDefinition("input_string", String)])
def my_solid(context, input_string):
    context.log.info(f"input string: {input_string}")


@pipeline
def my_pipeline():
    my_solid()


# def_end_marker


def execute_with_config():
    # execute_start_marker
    execute_pipeline(
        my_pipeline,
        run_config={"solids": {"my_solid": {"inputs": {"input_string": {"value": "marmot"}}}}},
    )
    # execute_end_marker
