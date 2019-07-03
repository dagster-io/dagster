from dagster import PipelineDefinition, OutputDefinition, lambda_solid, String
from dagster.core.definitions import create_environment_schema


def test_materialization_schema_types():
    @lambda_solid(output_def=OutputDefinition(String))
    def return_one():
        return 1

    pipeline_def = PipelineDefinition(
        name='test_materialization_schema_types', solid_defs=[return_one]
    )

    environment_schema = create_environment_schema(pipeline_def)

    string_mat_schema = environment_schema.config_type_named('String.MaterializationSchema')

    string_json_mat_schema = string_mat_schema.fields['json'].config_type

    assert environment_schema.config_type_keyed(string_json_mat_schema.key)
