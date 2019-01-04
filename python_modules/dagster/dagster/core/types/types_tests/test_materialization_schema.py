from dagster import (
    PipelineDefinition,
    OutputDefinition,
    lambda_solid,
    types,
)


def test_materialization_schema_types():
    @lambda_solid(output=OutputDefinition(types.Int))
    def return_one():
        return 1

    pipeline_def = PipelineDefinition(name='test_materialization_schema_types', solids=[return_one])

    string_mat_schema = pipeline_def.type_named('String.MaterializationSchema')

    string_json_mat_schema = string_mat_schema.field_dict['json'].dagster_type

    print(string_json_mat_schema.name)
    print(string_json_mat_schema.field_dict)

    assert pipeline_def.type_named(string_json_mat_schema.name)