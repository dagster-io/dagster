from dagster import pipeline, solid


@solid(config_schema={"iterations": int})
def configurable_solid_with_schema(context):
    for _ in range(context.solid_config["iterations"]):
        context.log.info(context.solid_config["word"])


@pipeline
def configurable_pipeline_with_schema():
    configurable_solid_with_schema()
