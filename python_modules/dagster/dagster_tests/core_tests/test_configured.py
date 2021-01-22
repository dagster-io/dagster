from dagster import ModeDefinition, execute_pipeline, pipeline, resource, solid


def test_configured_solids_and_resources():
    # idiomatic usage
    @solid(config_schema={"greeting": str}, required_resource_keys={"animal", "plant"})
    def emit_greet_creature(context):
        greeting = context.solid_config["greeting"]
        return f"{greeting}, {context.resources.animal}, {context.resources.plant}"

    emit_greet_salutation = emit_greet_creature.configured(
        {"greeting": "salutation"}, "emit_greet_salutation"
    )

    emit_greet_howdy = emit_greet_creature.configured({"greeting": "howdy"}, "emit_greet_howdy")

    @resource(config_schema={"creature": str})
    def emit_creature(context):
        return context.resource_config["creature"]

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={
                    "animal": emit_creature.configured({"creature": "dog"}),
                    "plant": emit_creature.configured({"creature": "tree"}),
                }
            )
        ]
    )
    def mypipeline():
        return emit_greet_salutation(), emit_greet_howdy()

    result = execute_pipeline(mypipeline)

    assert result.success
