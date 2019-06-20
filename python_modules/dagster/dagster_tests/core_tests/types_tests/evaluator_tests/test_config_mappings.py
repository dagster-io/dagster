# pylint: disable=no-value-for-parameter

import pytest

from dagster import (
    composite_solid,
    execute_pipeline,
    pipeline,
    solid,
    Field,
    PipelineConfigEvaluationError,
    Result,
    String,
)
from dagster.core.errors import DagsterUserCodeExecutionError


def wrap_config_mapping_fn(cfg):
    ensure_keypath_exists(cfg, ['solids'])
    cfg['solids']['scalar_config_solid'] = {'config': 'override'}
    return cfg


def bad_wrap_config_mapping_fn(cfg):
    ensure_keypath_exists(cfg, ['solids'])
    cfg['solids']['scalar_config_solid'] = {'config': 1234}
    return cfg


def raises_config_mapping_fn(_):
    assert 0


def nesting_config_mapping_fn(cfg):
    ensure_keypath_exists(cfg, ['solids', 'wrap', 'solids', 'scalar_config_solid'])
    cfg['solids']['wrap']['solids']['scalar_config_solid'] = {'config': 'nesting_override'}
    return cfg


@solid(config_field=Field(String, is_optional=True))
def scalar_config_solid(context):
    yield Result(context.solid_config)


@composite_solid(config_mapping_fn=wrap_config_mapping_fn)
def wrap():
    return scalar_config_solid()


@composite_solid(config_mapping_fn=nesting_config_mapping_fn)
def nesting_wrap():
    return wrap()


def ensure_keypath_exists(dst_dict, keys):
    if keys:
        key, rest = keys[0], keys[1:]
        dst_dict[key] = dst_dict.get(key, {})
        ensure_keypath_exists(dst_dict[key], rest)


def test_multiple_overrides_pipeline():
    @pipeline
    def wrap_pipeline():
        return nesting_wrap.alias('outer_wrap')()

    result = execute_pipeline(
        wrap_pipeline,
        {
            'solids': {
                'outer_wrap': {
                    'solids': {'wrap': {'solids': {'scalar_config_solid': {'config': 'test'}}}}
                }
            },
            'loggers': {'console': {'config': {'log_level': 'ERROR'}}},
        },
    )

    output_event = [e for e in result.step_event_list if e.event_type_value == 'STEP_OUTPUT'][0]
    assert output_event.event_specific_data.value_repr == "'nesting_override'"


def test_good_override():
    @pipeline
    def wrap_pipeline():
        return wrap.alias('do_stuff')()

    result = execute_pipeline(
        wrap_pipeline,
        {
            'solids': {'do_stuff': {'solids': {'scalar_config_solid': {'config': 'test'}}}},
            'loggers': {'console': {'config': {'log_level': 'ERROR'}}},
        },
    )

    assert result.success


def test_bad_override():
    @composite_solid(config_mapping_fn=bad_wrap_config_mapping_fn)
    def bad_wrap():
        return scalar_config_solid()

    @pipeline
    def wrap_pipeline():
        return bad_wrap.alias('do_stuff')()

    with pytest.raises(PipelineConfigEvaluationError) as exc_info:
        execute_pipeline(
            wrap_pipeline,
            {
                'solids': {'do_stuff': {'solids': {'scalar_config_solid': {'config': 'test'}}}},
                'loggers': {'console': {'config': {'log_level': 'ERROR'}}},
            },
        )

    assert len(exc_info.value.errors) == 1

    assert exc_info.value.errors[0].message == (
        '''Config override mapping function defined by solid do_stuff from definition bad_wrap at'''
        ''' path root:solids:do_stuff caused error: Value at path '''
        '''root:solids:scalar_config_solid:config is not valid. Expected "String"'''
    )


def test_raises_fn_override():
    @composite_solid(config_mapping_fn=raises_config_mapping_fn)
    def bad_wrap():
        return scalar_config_solid()

    @pipeline
    def wrap_pipeline():
        return bad_wrap.alias('do_stuff')()

    with pytest.raises(DagsterUserCodeExecutionError) as exc_info:
        execute_pipeline(
            wrap_pipeline,
            {
                'solids': {'do_stuff': {'solids': {'scalar_config_solid': {'config': 'test'}}}},
                'loggers': {'console': {'config': {'log_level': 'ERROR'}}},
            },
        )

    assert exc_info.match(
        'error occurred during execution of user config mapping function defined at path '
        'root:solids:do_stuff'
    )
