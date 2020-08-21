from dagster import Field, configured, solid


@solid(
    config_schema={"iterations": int, "word": Field(str, is_required=False, default_value="hello")}
)
def example_solid(context):
    for _ in range(context.solid_config["iterations"]):
        context.log.info(context.solid_config["word"])


# returns a solid named 'example_solid'
new_solid = configured(example_solid)({"iterations": 6, "word": "wheaties"})

# returns a solid named 'configured_example_solid'
another_new_solid = configured(example_solid, name="configured_example")(
    {"iterations": 6, "word": "wheaties"}
)
