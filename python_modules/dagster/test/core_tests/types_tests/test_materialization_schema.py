from dagster import PipelineDefinition, OutputDefinition, lambda_solid, types


def test_materialization_schema_types():
    @lambda_solid(output=OutputDefinition(types.String))
    def return_one():
        return 1

    pipeline_def = PipelineDefinition(name='test_materialization_schema_types', solids=[return_one])

    string_mat_schema = pipeline_def.config_type_named('String.MaterializationSchema')

    string_json_mat_schema = string_mat_schema.fields['json'].config_type

    assert pipeline_def.config_type_named(string_json_mat_schema.name)
