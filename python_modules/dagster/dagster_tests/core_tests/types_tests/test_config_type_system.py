from collections import namedtuple

import pytest

from dagster import (
    Any,
    DagsterEvaluateConfigValueError,
    Dict,
    ExecutionContext,
    Field,
    Int,
    List,
    Nullable,
    PipelineConfigEvaluationError,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    String,
    execute_pipeline,
    solid,
)


from dagster.core.types.evaluator import evaluate_config_value, DagsterEvaluationErrorReason

from dagster.core.test_utils import throwing_evaluate_config_value


def test_noop_config():
    assert Field(Any)


def test_int_field():
    config_field = Field(Dict({'int_field': Field(Int)}))

    assert evaluate_config_value(config_field.config_type, {'int_field': 1}).value == {
        'int_field': 1
    }


def assert_config_value_success(config_type, config_value, expected):
    result = evaluate_config_value(config_type, config_value)
    assert result.success
    assert result.value == expected


def assert_eval_failure(config_type, value):
    assert not evaluate_config_value(config_type, value).success


def test_int_fails():
    config_field = Field(Dict({'int_field': Field(Int)}))

    assert_eval_failure(config_field.config_type, {'int_field': 'fjkdj'})
    assert_eval_failure(config_field.config_type, {'int_field': True})


def test_default_arg():
    config_field = Field(Dict({'int_field': Field(Int, default_value=2, is_optional=True)}))

    assert_config_value_success(config_field.config_type, {}, {'int_field': 2})


def _single_required_string_config_dict():
    return Field(Dict({'string_field': Field(String)}))


def _multiple_required_fields_config_dict():
    return Field(Dict({'field_one': Field(String), 'field_two': Field(String)}))


def _single_optional_string_config_dict():
    return Field(Dict({'optional_field': Field(String, is_optional=True)}))


def _single_optional_string_field_config_dict_with_default():
    optional_field_def = Field(String, is_optional=True, default_value='some_default')
    return Field(Dict({'optional_field': optional_field_def}))


def _mixed_required_optional_string_config_dict_with_default():
    return Field(
        Dict(
            {
                'optional_arg': Field(String, is_optional=True, default_value='some_default'),
                'required_arg': Field(String, is_optional=False),
                'optional_arg_no_default': Field(String, is_optional=True),
            }
        )
    )


def _validate(config_field, value):
    return throwing_evaluate_config_value(config_field.config_type, value)


def test_single_required_string_field_config_type():
    assert _validate(_single_required_string_config_dict(), {'string_field': 'value'}) == {
        'string_field': 'value'
    }

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {'extra': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {'string_field': 'yupup', 'extra': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {'string_field': 1})


def test_multiple_required_fields_passing():
    assert _validate(
        _multiple_required_fields_config_dict(),
        {'field_one': 'value_one', 'field_two': 'value_two'},
    ) == {'field_one': 'value_one', 'field_two': 'value_two'}


def test_multiple_required_fields_failing():
    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_multiple_required_fields_config_dict(), {})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_multiple_required_fields_config_dict(), {'field_one': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_multiple_required_fields_config_dict(), {'field_one': 'yup', 'extra': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(
            _multiple_required_fields_config_dict(), {'field_one': 'value_one', 'field_two': 2}
        )


def test_single_optional_field_passing():
    assert _validate(_single_optional_string_config_dict(), {'optional_field': 'value'}) == {
        'optional_field': 'value'
    }
    assert _validate(_single_optional_string_config_dict(), {}) == {}

    with pytest.raises(DagsterEvaluateConfigValueError):
        assert _validate(_single_optional_string_config_dict(), {'optional_field': None}) == {
            'optional_field': None
        }


def test_single_optional_field_failing():
    with pytest.raises(DagsterEvaluateConfigValueError):

        _validate(_single_optional_string_config_dict(), {'optional_field': 1})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_optional_string_config_dict(), {'dlkjfalksdjflksaj': 1})


def test_single_optional_field_passing_with_default():
    assert _validate(_single_optional_string_field_config_dict_with_default(), {}) == {
        'optional_field': 'some_default'
    }

    assert _validate(
        _single_optional_string_field_config_dict_with_default(), {'optional_field': 'override'}
    ) == {'optional_field': 'override'}


def test_mixed_args_passing():
    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(),
        {'optional_arg': 'value_one', 'required_arg': 'value_two'},
    ) == {'optional_arg': 'value_one', 'required_arg': 'value_two'}

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(), {'required_arg': 'value_two'}
    ) == {'optional_arg': 'some_default', 'required_arg': 'value_two'}

    assert _validate(
        _mixed_required_optional_string_config_dict_with_default(),
        {'required_arg': 'value_two', 'optional_arg_no_default': 'value_three'},
    ) == {
        'optional_arg': 'some_default',
        'required_arg': 'value_two',
        'optional_arg_no_default': 'value_three',
    }


def _single_nested_config():
    return Field(Dict({'nested': Field(Dict({'int_field': Field(Int)}))}))


def _nested_optional_config_with_default():
    return Field(
        Dict({'nested': Field(Dict({'int_field': Field(Int, is_optional=True, default_value=3)}))})
    )


def _nested_optional_config_with_no_default():
    nested_type = Dict({'int_field': Field(Int, is_optional=True)})
    return Field(Dict({'nested': Field(dagster_type=nested_type)}))


def test_single_nested_config():
    assert _validate(_single_nested_config(), {'nested': {'int_field': 2}}) == {
        'nested': {'int_field': 2}
    }


def test_single_nested_config_failures():
    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_nested_config(), {'nested': 'dkjfdk'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_nested_config(), {'nested': {'int_field': 'dkjfdk'}})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_nested_config(), {'nested': {'int_field': {'too_nested': 'dkjfdk'}}})


def test_nested_optional_with_default():
    assert _validate(_nested_optional_config_with_default(), {'nested': {'int_field': 2}}) == {
        'nested': {'int_field': 2}
    }

    assert _validate(_nested_optional_config_with_default(), {'nested': {}}) == {
        'nested': {'int_field': 3}
    }


def test_nested_optional_with_no_default():
    assert _validate(_nested_optional_config_with_no_default(), {'nested': {'int_field': 2}}) == {
        'nested': {'int_field': 2}
    }

    assert _validate(_nested_optional_config_with_no_default(), {'nested': {}}) == {'nested': {}}


def single_elem(ddict):
    return list(ddict.items())[0]


def test_build_optionality():
    optional_test_type = Field(
        Dict(
            {
                'required': Field(Dict({'value': Field(String)})),
                'optional': Field(Dict({'value': Field(String, is_optional=True)})),
            }
        )
    ).config_type

    assert optional_test_type.fields['required'].is_optional is False
    assert optional_test_type.fields['optional'].is_optional is True


def test_wrong_solid_name():
    pipeline_def = PipelineDefinition(
        name='pipeline_wrong_solid_name',
        solids=[
            SolidDefinition(
                name='some_solid',
                inputs=[],
                outputs=[],
                config_field=Field(Int),
                transform_fn=lambda *_args: None,
            )
        ],
    )

    env_config = {'solids': {'another_name': {'config': {}}}}

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, env_config)

    pe = pe_info.value

    assert 'Undefined field "another_name" at path root:solids' in str(pe)


def fail_me():
    assert False
    return None


def test_multiple_context():
    pipeline_def = PipelineDefinition(
        name='pipeline_test_multiple_context',
        context_definitions={
            'context_one': PipelineContextDefinition(context_fn=lambda *_args: fail_me()),
            'context_two': PipelineContextDefinition(context_fn=lambda *_args: fail_me()),
        },
        solids=[],
    )

    with pytest.raises(PipelineConfigEvaluationError):
        execute_pipeline(pipeline_def, {'context': {'context_one': {}, 'context_two': {}}})


def test_wrong_context():
    pipeline_def = PipelineDefinition(
        name='pipeline_test_multiple_context',
        context_definitions={
            'context_one': PipelineContextDefinition(context_fn=lambda *_args: fail_me()),
            'context_two': PipelineContextDefinition(context_fn=lambda *_args: fail_me()),
        },
        solids=[],
    )

    with pytest.raises(
        PipelineConfigEvaluationError, match='Undefined field "nope" at path root:context'
    ):
        execute_pipeline(pipeline_def, {'context': {'nope': {}}})


def test_solid_list_config():
    value = [1, 2]
    called = {}

    def _test_config(info, _inputs):
        assert info.config == value
        called['yup'] = True

    pipeline_def = PipelineDefinition(
        name='solid_list_config_pipeline',
        solids=[
            SolidDefinition(
                name='solid_list_config',
                inputs=[],
                outputs=[],
                config_field=Field(List(Int)),
                transform_fn=_test_config,
            )
        ],
    )

    result = execute_pipeline(
        pipeline_def, environment={'solids': {'solid_list_config': {'config': value}}}
    )

    assert result.success
    assert called['yup']


def test_two_list_types():
    assert PipelineDefinition(
        name='two_types',
        solids=[
            SolidDefinition(
                name='two_list_type',
                inputs=[],
                outputs=[],
                config_field=Field(
                    Dict({'list_one': Field(List(Int)), 'list_two': Field(List(Int))})
                ),
                transform_fn=lambda *_args: None,
            )
        ],
    )


def test_multilevel_default_handling():
    @solid(config_field=Field(Int, is_optional=True, default_value=234))
    def has_default_value(info):
        assert info.config == 234

    pipeline_def = PipelineDefinition(
        name='multilevel_default_handling', solids=[has_default_value]
    )

    assert execute_pipeline(pipeline_def).success
    assert execute_pipeline(pipeline_def, environment=None).success
    assert execute_pipeline(pipeline_def, environment={}).success
    assert execute_pipeline(pipeline_def, environment={'solids': None}).success
    assert execute_pipeline(pipeline_def, environment={'solids': {}}).success
    assert execute_pipeline(
        pipeline_def, environment={'solids': {'has_default_value': None}}
    ).success

    assert execute_pipeline(pipeline_def, environment={'solids': {'has_default_value': {}}}).success

    assert execute_pipeline(
        pipeline_def, environment={'solids': {'has_default_value': {'config': 234}}}
    ).success


def test_no_env_missing_required_error_handling():
    @solid(config_field=Field(Int))
    def required_int_solid(_info):
        pass

    pipeline_def = PipelineDefinition(
        name='no_env_missing_required_error', solids=[required_int_solid]
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def)

    assert isinstance(pe_info.value, PipelineConfigEvaluationError)
    pe = pe_info.value
    assert len(pe.errors) == 1
    mfe = pe.errors[0]
    assert mfe.reason == DagsterEvaluationErrorReason.MISSING_REQUIRED_FIELD
    assert len(pe.error_messages) == 1

    assert 'Missing required field "solids"' in pe.message
    assert 'at document config root' in pe.message
    assert 'Missing required field "solids"' in pe.error_messages[0]


def test_root_extra_field():
    @solid(config_field=Field(Int))
    def required_int_solid(_info):
        pass

    pipeline_def = PipelineDefinition(name='root_extra_field', solids=[required_int_solid])

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def,
            environment={'solids': {'required_int_solid': {'config': 948594}}, 'nope': None},
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    fnd = pe.errors[0]
    assert fnd.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert 'Undefined field "nope"' in pe.message


def test_deeper_path():
    @solid(config_field=Field(Int))
    def required_int_solid(_info):
        pass

    pipeline_def = PipelineDefinition(name='deeper_path', solids=[required_int_solid])

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def, environment={'solids': {'required_int_solid': {'config': 'asdf'}}}
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    rtm = pe.errors[0]
    assert rtm.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_working_list_path():
    called = {}

    @solid(config_field=Field(List(Int)))
    def required_list_int_solid(info):
        assert info.config == [1, 2]
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='list_path', solids=[required_list_int_solid])

    result = execute_pipeline(
        pipeline_def, environment={'solids': {'required_list_int_solid': {'config': [1, 2]}}}
    )

    assert result.success
    assert called['yup']


def test_item_error_list_path():
    called = {}

    @solid(config_field=Field(List(Int)))
    def required_list_int_solid(info):
        assert info.config == [1, 2]
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='list_path', solids=[required_list_int_solid])

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def,
            environment={'solids': {'required_list_int_solid': {'config': [1, 'nope']}}},
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    rtm = pe.errors[0]
    assert rtm.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH

    assert 'Type failure at path "root:solids:required_list_int_solid:config[1]"' in str(pe)


def test_context_selector_working():
    called = {}

    @solid
    def check_context(info):
        assert info.context.resources == 32
        called['yup'] = True

    pipeline_def = PipelineDefinition(
        name='context_selector_working',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda info: ExecutionContext(resources=info.config),
                config_field=Field(Int),
            )
        },
    )

    result = execute_pipeline(
        pipeline_def, environment={'context': {'context_required_int': {'config': 32}}}
    )

    assert result.success
    assert called['yup']


def test_context_selector_extra_context():
    @solid
    def check_context(_info):
        assert False

    pipeline_def = PipelineDefinition(
        name='context_selector_extra_context',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda info: ExecutionContext(resources=info.config),
                config_field=Field(Int),
            )
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def,
            environment={
                'context': {
                    'context_required_int': {'config': 32},
                    'extra_context': {'config': None},
                }
            },
        )

    pe = pe_info.value
    cse = pe.errors[0]
    assert cse.reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR
    assert 'Specified more than one field at path "root:context"' in str(pe)


def test_context_selector_wrong_name():
    @solid
    def check_context(_info):
        assert False

    pipeline_def = PipelineDefinition(
        name='context_selector_wrong_name',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda info: ExecutionContext(resources=info.config),
                config_field=Field(Int),
            )
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment={'context': {'wrong_name': {'config': None}}})

    pe = pe_info.value
    cse = pe.errors[0]
    assert cse.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert 'Undefined field "wrong_name" at path root:context' in str(pe)


def test_context_selector_none_given():
    @solid
    def check_context(_info):
        assert False

    pipeline_def = PipelineDefinition(
        name='context_selector_none_given',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda info: ExecutionContext(resources=info.config),
                config_field=Field(Int),
            )
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment={'context': None})

    pe = pe_info.value
    cse = pe.errors[0]
    assert cse.reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR
    assert 'You specified no fields at path "root:context"' in str(pe)


def test_multilevel_good_error_handling_solids():
    @solid(config_field=Field(Int))
    def good_error_handling(_info):
        pass

    pipeline_def = PipelineDefinition(
        name='multilevel_good_error_handling', solids=[good_error_handling]
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment={'solids': None})

    pe = pe_info.value
    assert 'Missing required field "good_error_handling" at path root:solids' in str(pe)


def test_multilevel_good_error_handling_solid_name_solids():
    @solid(config_field=Field(Int))
    def good_error_handling(_info):
        pass

    pipeline_def = PipelineDefinition(
        name='multilevel_good_error_handling', solids=[good_error_handling]
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment={'solids': {'good_error_handling': {}}})

    pe = pe_info.value
    assert 'Missing required field "config" at path root:solids:good_error_handling' in str(pe)


def test_multilevel_good_error_handling_config_solids_name_solids():
    @solid(config_field=Field(Nullable(Int)))
    def good_error_handling(_info):
        pass

    pipeline_def = PipelineDefinition(
        name='multilevel_good_error_handling', solids=[good_error_handling]
    )

    execute_pipeline(
        pipeline_def, environment={'solids': {'good_error_handling': {'config': None}}}
    )
