from dagster import pipeline, solid


@solid
def config_example_solid(context):
    for _ in range(context.solid_config["iterations"]):
        context.log.info("hello")


@pipeline
def config_example_pipeline():
    config_example_solid()
