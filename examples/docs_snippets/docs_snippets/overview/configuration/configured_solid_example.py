from dagster import Field, configured, solid


@solid(
    config_schema={"iterations": int, "word": Field(str, is_required=False, default_value="hello")}
)
def example_solid(context):
    for _ in range(context.solid_config["iterations"]):
        context.log.info(context.solid_config["word"])


# This example is fully configured. With this syntax, a name must be explicitly provided.
configured_example = configured(example_solid, name="configured_example")(
    {"iterations": 6, "word": "wheaties"}
)

# This example is partially configured: `iterations` is passed through
# The decorator yields a solid named 'another_configured_example' (from the decorated function)
# with `int` as the `config_schema`.
@configured(example_solid, int)
def another_configured_example(config):
    return {"iterations": config, "word": "wheaties"}
