import re
import sys

import pytest

from dagster import (
    DagsterTypeCheckError,
    EventMetadataEntry,
    InputDefinition,
    Int,
    List,
    Optional,
    OutputDefinition,
    TypeCheck,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.core.types.dagster_type import DagsterType, PythonObjectType, resolve_dagster_type


class BarObj(object):
    pass


class _Bar(PythonObjectType):
    def __init__(self):
        super(_Bar, self).__init__(BarObj, name='Bar', description='A bar.')


Bar = _Bar()


def test_python_object_type():
    type_bar = Bar

    assert type_bar.name == 'Bar'
    assert type_bar.description == 'A bar.'
    assert_success(type_bar, BarObj())

    assert_failure(type_bar, None)

    assert_failure(type_bar, 'not_a_bar')


def test_python_object_type_with_custom_type_check():
    def eq_3(value):
        return isinstance(value, int) and value == 3

    Int3 = DagsterType(name='Int3', type_check_fn=eq_3)

    assert Int3.name == 'Int3'
    assert_success(Int3, 3)
    assert_failure(Int3, 5)


def test_nullable_python_object_type():
    nullable_type_bar = resolve_dagster_type(Optional[Bar])

    assert_type_check(nullable_type_bar.type_check(BarObj()))
    assert_type_check(nullable_type_bar.type_check(None))

    res = nullable_type_bar.type_check('not_a_bar')
    assert not res.success


def test_nullable_int_coercion():
    int_type = resolve_dagster_type(Int)
    assert_type_check(int_type.type_check(1))

    res = int_type.type_check(None)
    assert not res.success

    nullable_int_type = resolve_dagster_type(Optional[Int])
    assert_type_check(nullable_int_type.type_check(1))
    assert_type_check(nullable_int_type.type_check(None))


def assert_type_check(type_check):
    assert isinstance(type_check, TypeCheck) and type_check.success


def assert_success(runtime_type, value):
    type_check_result = runtime_type.type_check(value)
    assert_type_check(type_check_result)


def assert_failure(runtime_type, value):
    res = runtime_type.type_check(value)
    assert not res.success


def test_nullable_list_combos_coerciion():

    list_of_int = resolve_dagster_type(List[Int])

    assert_failure(list_of_int, None)
    assert_success(list_of_int, [])
    assert_success(list_of_int, [1])
    assert_failure(list_of_int, [None])

    nullable_int_of_list = resolve_dagster_type(Optional[List[Int]])

    assert_success(nullable_int_of_list, None)
    assert_success(nullable_int_of_list, [])
    assert_success(nullable_int_of_list, [1])
    assert_failure(nullable_int_of_list, [None])

    list_of_nullable_int = resolve_dagster_type(List[Optional[Int]])
    assert_failure(list_of_nullable_int, None)
    assert_success(list_of_nullable_int, [])
    assert_success(list_of_nullable_int, [1])
    assert_success(list_of_nullable_int, [None])

    nullable_list_of_nullable_int = resolve_dagster_type(Optional[List[Optional[Int]]])
    assert_success(nullable_list_of_nullable_int, None)
    assert_success(nullable_list_of_nullable_int, [])
    assert_success(nullable_list_of_nullable_int, [1])
    assert_success(nullable_list_of_nullable_int, [None])


def execute_no_throw(pipeline_def):
    return execute_pipeline(pipeline_def, raise_on_error=False)


def _type_check_data_for_input(solid_result, input_name):
    return solid_result.compute_input_event_dict[input_name].event_specific_data.type_check_data


def test_input_types_succeed_in_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('num', int)])
    def take_num(num):
        return num

    @pipeline
    def pipe():
        return take_num(return_one())

    pipeline_result = execute_pipeline(pipe)
    assert pipeline_result.success

    solid_result = pipeline_result.result_for_solid('take_num')
    assert solid_result.success

    type_check_data = _type_check_data_for_input(solid_result, 'num')
    assert type_check_data.success


def test_output_types_succeed_in_pipeline():
    @lambda_solid(output_def=OutputDefinition(int))
    def return_one():
        return 1

    @pipeline
    def pipe():
        return return_one()

    pipeline_result = execute_pipeline(pipe)
    assert pipeline_result.success

    solid_result = pipeline_result.result_for_solid('return_one')
    assert solid_result.success

    output_event = solid_result.get_output_event_for_compute()
    type_check_data = output_event.event_specific_data.type_check_data
    assert type_check_data.success


def test_input_types_fail_in_pipeline():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('string', str)])
    def take_string(string):
        return string

    @pipeline
    def pipe():
        return take_string(return_one())

    with pytest.raises(DagsterTypeCheckError) as exc_info:
        execute_pipeline(pipe)

    assert 'In solid "take_string" the input "string" received value 1 of Python ' in str(
        exc_info.value
    )

    # now check events in no throw case

    pipeline_result = execute_no_throw(pipe)

    assert not pipeline_result.success

    solid_result = pipeline_result.result_for_solid('take_string')

    type_check_data = _type_check_data_for_input(solid_result, 'string')
    assert not type_check_data.success
    assert type_check_data.description == 'Value "1" of python type "int" must be a string.'

    step_failure_event = solid_result.compute_step_failure_event
    assert step_failure_event.event_specific_data.error.cls_name == 'Failure'


def test_output_types_fail_in_pipeline():
    @lambda_solid(output_def=OutputDefinition(str))
    def return_int_fails():
        return 1

    @pipeline
    def pipe():
        return return_int_fails()

    with pytest.raises(DagsterTypeCheckError) as exc_info:
        execute_pipeline(pipe)

    assert (
        'In solid "return_int_fails" the output "result" received value 1 of Python type'
    ) in str(exc_info.value)

    pipeline_result = execute_no_throw(pipe)

    assert not pipeline_result.success

    solid_result = pipeline_result.result_for_solid('return_int_fails')

    assert not solid_result.success

    output_event = solid_result.get_output_event_for_compute()
    type_check_data = output_event.event_specific_data.type_check_data
    assert not type_check_data.success
    assert type_check_data.description == 'Value "1" of python type "int" must be a string.'

    step_failure_event = solid_result.compute_step_failure_event
    assert step_failure_event.event_specific_data.error.cls_name == 'Failure'


# TODO add more step output use cases


def _always_fails(_value):
    raise Exception('kdjfkjd')


ThrowsExceptionType = DagsterType(name='ThrowsExceptionType', type_check_fn=_always_fails,)


def _return_bad_value(_value):
    return 'kdjfkjd'


BadType = DagsterType(name='BadType', type_check_fn=_return_bad_value)


def test_input_type_returns_wrong_thing():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('value', BadType)])
    def take_bad_thing(value):
        return value

    @pipeline
    def pipe():
        return take_bad_thing(return_one())

    # when https://github.com/dagster-io/dagster/issues/2018 is resolve
    # the two error messages in the test should be the same
    with pytest.raises(
        DagsterTypeCheckError,
        match=re.escape(
            'In solid "take_bad_thing" the input "value" received value 1 of Python type <'
        )
        + '(class|type)'
        + re.escape(
            ' \'int\'> which does not pass the typecheck for Dagster type BadType. Step '
            'take_bad_thing.compute.'
        ),
    ):
        execute_pipeline(pipe)

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success

    solid_result = pipeline_result.result_for_solid('take_bad_thing')
    type_check_data = _type_check_data_for_input(solid_result, 'value')
    assert not type_check_data.success
    if sys.version_info.major == 3:
        assert type_check_data.description == (
            "You have returned 'kdjfkjd' of type <class 'str'> from the "
            "type check function of type \"BadType\". Return value must be instance of "
            "TypeCheck or a bool."
        )
    else:
        assert type_check_data.description == (
            "You have returned 'kdjfkjd' of type <type 'str'> from the "
            "type check function of type \"BadType\". Return value must be instance of "
            "TypeCheck or a bool."
        )
    assert not type_check_data.metadata_entries

    step_failure_event = solid_result.compute_step_failure_event
    assert step_failure_event.event_specific_data.error.cls_name == 'Failure'


def test_output_type_returns_wrong_thing():
    @lambda_solid(output_def=OutputDefinition(BadType))
    def return_one_bad_thing():
        return 1

    @pipeline
    def pipe():
        return return_one_bad_thing()

    # when https://github.com/dagster-io/dagster/issues/2018 is resolve
    # the two error messages in the test should be the same
    with pytest.raises(
        DagsterTypeCheckError,
        match=re.escape(
            'In solid "return_one_bad_thing" the output "result" received value 1 of Python type <'
        )
        + '(class|type)'
        + re.escape(
            ' \'int\'> which does not pass the typecheck for Dagster type BadType. Step '
            'return_one_bad_thing.compute.'
        ),
    ):
        execute_pipeline(pipe)

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success

    solid_result = pipeline_result.result_for_solid('return_one_bad_thing')
    output_event = solid_result.get_output_event_for_compute()
    type_check_data = output_event.event_specific_data.type_check_data
    assert not type_check_data.success

    if sys.version_info.major == 3:
        assert type_check_data.description == (
            "You have returned 'kdjfkjd' of type <class 'str'> from the "
            "type check function of type \"BadType\". Return value must be instance of "
            "TypeCheck or a bool."
        )
    else:
        assert type_check_data.description == (
            "You have returned 'kdjfkjd' of type <type 'str'> from the "
            "type check function of type \"BadType\". Return value must be instance of "
            "TypeCheck or a bool."
        )

    step_failure_event = solid_result.compute_step_failure_event
    assert step_failure_event.event_specific_data.error.cls_name == 'Failure'


def test_input_type_throw_arbitrary_exception():
    @lambda_solid
    def return_one():
        return 1

    @lambda_solid(input_defs=[InputDefinition('value', ThrowsExceptionType)])
    def take_throws(value):
        return value

    @pipeline
    def pipe():
        return take_throws(return_one())

    with pytest.raises(DagsterTypeCheckError):
        execute_pipeline(pipe)

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success
    solid_result = pipeline_result.result_for_solid('take_throws')
    type_check_data = _type_check_data_for_input(solid_result, 'value')
    assert not type_check_data.success

    step_failure_event = solid_result.compute_step_failure_event
    assert step_failure_event.event_specific_data.error.cls_name == 'Failure'


def test_output_type_throw_arbitrary_exception():
    @lambda_solid(output_def=OutputDefinition(ThrowsExceptionType))
    def return_one_throws():
        return 1

    @pipeline
    def pipe():
        return return_one_throws()

    with pytest.raises(DagsterTypeCheckError):
        execute_pipeline(pipe)

    pipeline_result = execute_no_throw(pipe)
    assert not pipeline_result.success
    solid_result = pipeline_result.result_for_solid('return_one_throws')

    output_event = solid_result.get_output_event_for_compute()
    type_check_data = output_event.event_specific_data.type_check_data
    assert not type_check_data.success

    assert 'kdjfkjd' == type_check_data.description

    step_failure_event = solid_result.compute_step_failure_event
    assert step_failure_event.event_specific_data.error.cls_name == 'Failure'


def define_custom_dict(name, permitted_key_names):
    def type_check_method(value):
        if not isinstance(value, dict):
            return TypeCheck(
                False,
                description='Value {value} should be of type {type_name}.'.format(
                    value=value, type_name=name
                ),
            )
        for key in value:
            if not key in permitted_key_names:
                return TypeCheck(
                    False,
                    description=(
                        'Key {name} is not a permitted value, values can only be of: ' '{name_list}'
                    ).format(name=value.name, name_list=permitted_key_names),
                )
        return TypeCheck(
            True,
            metadata_entries=[
                EventMetadataEntry.text(label='row_count', text=str(len(value))),
                EventMetadataEntry.text(label='series_names', text=', '.join(value.keys())),
            ],
        )

    return DagsterType(key=name, name=name, type_check_fn=type_check_method)


def test_fan_in_custom_types_with_storage():
    CustomDict = define_custom_dict('CustomDict', ['foo', 'bar'])

    @solid(output_defs=[OutputDefinition(CustomDict)])
    def return_dict_1(_context):
        return {'foo': 3}

    @solid(output_defs=[OutputDefinition(CustomDict)])
    def return_dict_2(_context):
        return {'bar': 'zip'}

    @solid(input_defs=[InputDefinition('dicts', List[CustomDict])])
    def get_foo(_context, dicts):
        return dicts[0]['foo']

    @pipeline
    def dict_pipeline():
        # Fan-in
        get_foo([return_dict_1(), return_dict_2()])

    pipeline_result = execute_pipeline(
        dict_pipeline, environment_dict={'storage': {'filesystem': {}}}
    )
    assert pipeline_result.success


ReturnBoolType = DagsterType(name='ReturnBoolType', type_check_fn=lambda _: True)


def test_return_bool_type():
    @solid(output_defs=[OutputDefinition(ReturnBoolType)])
    def return_always_pass_bool_type(_):
        return 1

    @pipeline
    def bool_type_pipeline():
        return_always_pass_bool_type()

    assert execute_pipeline(bool_type_pipeline).success
