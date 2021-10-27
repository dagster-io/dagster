from dagster import Field, configured, op


@op(config_schema={"iterations": int, "word": Field(str, is_required=False, default_value="hello")})
def example(context):
    for _ in range(context.op_config["iterations"]):
        context.log.info(context.op_config["word"])


# This example is fully configured. With this syntax, a name must be explicitly provided.
configured_example = configured(example, name="configured_example")(
    {"iterations": 6, "word": "wheaties"}
)

# This example is partially configured: `iterations` is passed through
# The decorator yields an op named 'another_configured_example' (from the decorated function)
# with `int` as the `config_schema`.
@configured(example, int)
def another_configured_example(config):
    return {"iterations": config, "word": "wheaties"}
