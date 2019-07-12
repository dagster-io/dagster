from dagster import PipelineDefinition, SolidDefinition, Field, Dict, String
from dagster.core.execution.api import create_execution_plan


def test_execution_plan_create_metadata():
    solid_def = SolidDefinition(
        name='solid_metadata_creation',
        input_defs=[],
        output_defs=[],
        compute_fn=lambda *args, **kwargs: None,
        config_field=Field(Dict({'str_value': Field(String)})),
        step_metadata_fn=lambda env_config: {
            'computed': env_config.solids['solid_metadata_creation'].config['str_value'] + '1'
        },
    )
    p_def = PipelineDefinition(name='test_metadata', solid_defs=[solid_def])

    execution_plan = create_execution_plan(
        p_def,
        environment_dict={
            'solids': {'solid_metadata_creation': {'config': {'str_value': 'foobar'}}}
        },
    )

    compute_step = execution_plan.get_step_by_key('solid_metadata_creation.compute')
    assert compute_step
    assert compute_step.metadata == {'computed': 'foobar1'}
