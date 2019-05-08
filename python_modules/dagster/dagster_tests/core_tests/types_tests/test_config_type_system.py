import pytest

from dagster import (
    check,
    Any,
    DagsterEvaluateConfigValueError,
    Dict,
    ExecutionContext,
    Field,
    Int,
    List,
    Nullable,
    PermissiveDict,
    PipelineConfigEvaluationError,
    PipelineContextDefinition,
    PipelineDefinition,
    SolidDefinition,
    String,
    execute_pipeline,
    solid,
)


from dagster.core.definitions import create_environment_schema
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


def _multiple_required_fields_config_permissive_dict():
    return Field(PermissiveDict({'field_one': Field(String), 'field_two': Field(String)}))


def _validate(config_field, value):
    return throwing_evaluate_config_value(config_field.config_type, value)


def test_single_required_string_field_config_type():
    assert _validate(_single_required_string_config_dict(), {'string_field': 'value'}) == {
        'string_field': 'value'
    }

    with pytest.raises(DagsterEvaluateConfigValueError) as top_error:
        _validate(_single_required_string_config_dict(), {})

    assert str(top_error.value) == (
        '''Missing required field "string_field" at document config root. '''
        '''Available Fields: "['string_field']".'''
    )

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {'extra': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {'string_field': 'yupup', 'extra': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_single_required_string_config_dict(), {'string_field': 1})


def test_undefined_field_error():
    with pytest.raises(
        DagsterEvaluateConfigValueError,
        match=(
            'Field "extra" is not defined at document config root. Expected: "{ string_field: '
            'String }"'
        ),
    ):
        _validate(
            _single_required_string_config_dict(), {'string_field': 'value', 'extra': 'extra'}
        )


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
            _multiple_required_fields_config_dict(),
            {'field_one': 'yup', 'field_two': 'yup', 'extra': 'should_not_exist'},
        )

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


def test_permissive_multiple_required_fields_passing():
    assert _validate(
        _multiple_required_fields_config_permissive_dict(),
        {
            'field_one': 'value_one',
            'field_two': 'value_two',
            'previously_unspecified': 'should_exist',
        },
    ) == {
        'field_one': 'value_one',
        'field_two': 'value_two',
        'previously_unspecified': 'should_exist',
    }


def test_permissive_multiple_required_fields_nested_passing():
    assert _validate(
        _multiple_required_fields_config_permissive_dict(),
        {
            'field_one': 'value_one',
            'field_two': 'value_two',
            'previously_unspecified': {'nested': 'value', 'with_int': 2},
        },
    ) == {
        'field_one': 'value_one',
        'field_two': 'value_two',
        'previously_unspecified': {'nested': 'value', 'with_int': 2},
    }


def test_permissive_multiple_required_fields_failing():
    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_multiple_required_fields_config_permissive_dict(), {})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(_multiple_required_fields_config_permissive_dict(), {'field_one': 'yup'})

    with pytest.raises(DagsterEvaluateConfigValueError):
        _validate(
            _multiple_required_fields_config_permissive_dict(),
            {'field_one': 'value_one', 'field_two': 2},
        )


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


def test_single_nested_config_undefined_errors():
    with pytest.raises(
        DagsterEvaluateConfigValueError,
        match='Value at path root:nested must be dict. Expected: "{ int_field: Int }".',
    ):
        _validate(_single_nested_config(), {'nested': 'dkjfdk'})

    with pytest.raises(
        DagsterEvaluateConfigValueError,
        match='Value at path root:nested:int_field is not valid. Expected "Int"',
    ):
        _validate(_single_nested_config(), {'nested': {'int_field': 'dkjfdk'}})

    with pytest.raises(
        DagsterEvaluateConfigValueError,
        match=(
            'Field "not_a_field" is not defined at path root:nested Expected: '
            '"{ int_field: Int }"'
        ),
    ):
        _validate(_single_nested_config(), {'nested': {'int_field': 2, 'not_a_field': 1}})

    with pytest.raises(
        DagsterEvaluateConfigValueError,
        match='Value at path root:nested:int_field is not valid. Expected "Int"',
    ):
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

    def _test_config(context, _inputs):
        assert context.solid_config == value
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
        pipeline_def, environment_dict={'solids': {'solid_list_config': {'config': value}}}
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
    def has_default_value(context):
        assert context.solid_config == 234

    pipeline_def = PipelineDefinition(
        name='multilevel_default_handling', solids=[has_default_value]
    )

    assert execute_pipeline(pipeline_def).success
    assert execute_pipeline(pipeline_def, environment_dict=None).success
    assert execute_pipeline(pipeline_def, environment_dict={}).success
    assert execute_pipeline(pipeline_def, environment_dict={'solids': None}).success
    assert execute_pipeline(pipeline_def, environment_dict={'solids': {}}).success
    assert execute_pipeline(
        pipeline_def, environment_dict={'solids': {'has_default_value': None}}
    ).success

    assert execute_pipeline(
        pipeline_def, environment_dict={'solids': {'has_default_value': {}}}
    ).success

    assert execute_pipeline(
        pipeline_def, environment_dict={'solids': {'has_default_value': {'config': 234}}}
    ).success


def test_no_env_missing_required_error_handling():
    @solid(config_field=Field(Int))
    def required_int_solid(_context):
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
    assert len(pe.errors) == 1

    assert pe.errors[0].message == (
        '''Missing required field "solids" at document config root. '''
        '''Available Fields: "['context', 'execution', 'expectations', '''
        ''''solids', 'storage']".'''
    )


def test_root_extra_field():
    @solid(config_field=Field(Int))
    def required_int_solid(_context):
        pass

    pipeline_def = PipelineDefinition(name='root_extra_field', solids=[required_int_solid])

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def,
            environment_dict={'solids': {'required_int_solid': {'config': 948594}}, 'nope': None},
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    fnd = pe.errors[0]
    assert fnd.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert 'Undefined field "nope"' in pe.message


def test_deeper_path():
    @solid(config_field=Field(Int))
    def required_int_solid(_context):
        pass

    pipeline_def = PipelineDefinition(name='deeper_path', solids=[required_int_solid])

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def, environment_dict={'solids': {'required_int_solid': {'config': 'asdf'}}}
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    rtm = pe.errors[0]
    assert rtm.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH


def test_working_list_path():
    called = {}

    @solid(config_field=Field(List(Int)))
    def required_list_int_solid(context):
        assert context.solid_config == [1, 2]
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='list_path', solids=[required_list_int_solid])

    result = execute_pipeline(
        pipeline_def, environment_dict={'solids': {'required_list_int_solid': {'config': [1, 2]}}}
    )

    assert result.success
    assert called['yup']


def test_item_error_list_path():
    called = {}

    @solid(config_field=Field(List(Int)))
    def required_list_int_solid(context):
        assert context.solid_config == [1, 2]
        called['yup'] = True

    pipeline_def = PipelineDefinition(name='list_path', solids=[required_list_int_solid])

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def,
            environment_dict={'solids': {'required_list_int_solid': {'config': [1, 'nope']}}},
        )

    pe = pe_info.value
    assert len(pe.errors) == 1
    rtm = pe.errors[0]
    assert rtm.reason == DagsterEvaluationErrorReason.RUNTIME_TYPE_MISMATCH

    assert 'Type failure at path "root:solids:required_list_int_solid:config[1]"' in str(pe)


def test_context_selector_working():
    called = {}

    @solid
    def check_context(context):
        assert context.resources == 32
        called['yup'] = True

    pipeline_def = PipelineDefinition(
        name='context_selector_working',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.context_config
                ),
                config_field=Field(Int),
            )
        },
    )

    result = execute_pipeline(
        pipeline_def, environment_dict={'context': {'context_required_int': {'config': 32}}}
    )

    assert result.success
    assert called['yup']


def test_context_selector_extra_context():
    @solid
    def check_context(_context):
        assert False

    pipeline_def = PipelineDefinition(
        name='context_selector_extra_context',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.solid_config
                ),
                config_field=Field(Int),
            )
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def,
            environment_dict={
                'context': {
                    'context_required_int': {'config': 32},
                    'extra_context': {'config': None},
                }
            },
        )

    pe = pe_info.value
    cse = pe.errors[0]
    assert cse.message == (
        '''You can only specify a single field at path root:context. '''
        '''You specified ['context_required_int', 'extra_context']. '''
        '''The available fields are ['context_required_int']'''
    )


def test_context_selector_wrong_name():
    @solid
    def check_context(_context):
        assert False

    pipeline_def = PipelineDefinition(
        name='context_selector_wrong_name',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.solid_config
                ),
                config_field=Field(Int),
            )
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(
            pipeline_def, environment_dict={'context': {'wrong_name': {'config': None}}}
        )

    pe = pe_info.value
    cse = pe.errors[0]
    assert cse.reason == DagsterEvaluationErrorReason.FIELD_NOT_DEFINED
    assert 'Undefined field "wrong_name" at path root:context' in str(pe)


def test_context_selector_none_given():
    @solid
    def check_context(_context):
        assert False

    pipeline_def = PipelineDefinition(
        name='context_selector_none_given',
        solids=[check_context],
        context_definitions={
            'context_required_int': PipelineContextDefinition(
                context_fn=lambda init_context: ExecutionContext(
                    resources=init_context.solid_config
                ),
                config_field=Field(Int),
            )
        },
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment_dict={'context': None})

    pe = pe_info.value
    cse = pe.errors[0]
    assert cse.reason == DagsterEvaluationErrorReason.SELECTOR_FIELD_ERROR
    assert cse.message == (
        '''Must specify the required field at path root:context. Defined '''
        '''fields: ['context_required_int']'''
    )


def test_multilevel_good_error_handling_solids():
    @solid(config_field=Field(Int))
    def good_error_handling(_context):
        pass

    pipeline_def = PipelineDefinition(
        name='multilevel_good_error_handling', solids=[good_error_handling]
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment_dict={'solids': None})

    assert len(pe_info.value.errors) == 1
    assert pe_info.value.errors[0].message == (
        '''Missing required field "good_error_handling" at path root:solids '''
        '''Available Fields: "['good_error_handling']".'''
    )


def test_multilevel_good_error_handling_solid_name_solids():
    @solid(config_field=Field(Int))
    def good_error_handling(_context):
        pass

    pipeline_def = PipelineDefinition(
        name='multilevel_good_error_handling', solids=[good_error_handling]
    )

    with pytest.raises(PipelineConfigEvaluationError) as pe_info:
        execute_pipeline(pipeline_def, environment_dict={'solids': {'good_error_handling': {}}})

    assert len(pe_info.value.errors) == 1
    assert pe_info.value.errors[0].message == (
        '''Missing required field "config" at path root:solids:good_error_handling '''
        '''Available Fields: "['config', 'outputs']".'''
    )


def test_multilevel_good_error_handling_config_solids_name_solids():
    @solid(config_field=Field(Nullable(Int)))
    def good_error_handling(_context):
        pass

    pipeline_def = PipelineDefinition(
        name='multilevel_good_error_handling', solids=[good_error_handling]
    )

    execute_pipeline(
        pipeline_def, environment_dict={'solids': {'good_error_handling': {'config': None}}}
    )


def test_invalid_default_values():
    with pytest.raises(check.ParameterCheckError):

        @solid(config_field=Field(Int, default_value='3'))
        def _solid():
            pass


def test_secret_field():
    @solid(
        config_field=Field(
            Dict({'password': Field(String, is_secret=True), 'notpassword': Field(String)})
        )
    )
    def solid_with_secret(_context):
        pass

    pipeline_def = PipelineDefinition(name='secret_pipeline', solids=[solid_with_secret])

    environment_schema = create_environment_schema(pipeline_def)
    config_type = environment_schema.config_type_named('SecretPipeline.SolidConfig.SolidWithSecret')

    assert config_type

    password_field = config_type.fields['config'].config_type.fields['password']

    assert password_field.is_secret

    notpassword_field = config_type.fields['config'].config_type.fields['notpassword']

    assert not notpassword_field.is_secret
