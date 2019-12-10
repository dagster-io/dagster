import re

import pytest

from dagster import (
    DagsterTypeCheckError,
    EventMetadataEntry,
    InputDefinition,
    OutputDefinition,
    TypeCheck,
    execute_pipeline,
    lambda_solid,
    pipeline,
    solid,
)
from dagster.core.types import Int, List, Optional, PythonObjectType
from dagster.core.types.runtime import RuntimeType, resolve_to_runtime_type


class BarObj(object):
    pass


class Bar(PythonObjectType):
    def __init__(self):
        super(Bar, self).__init__(BarObj, description='A bar.')


def test_python_object_type():
    type_bar = Bar.inst()

    assert type_bar.name == 'Bar'
    assert type_bar.description == 'A bar.'
    assert_success(type_bar, BarObj())

    assert_failure(type_bar, None)

    assert_failure(type_bar, 'not_a_bar')


def test_python_object_type_with_custom_type_check():
    def eq_3(value):
        if value != 3:
            return False
        return True

    class Int3(PythonObjectType):
        def __init__(self):
            super(Int3, self).__init__(int, type_check=eq_3)

    type_int_3 = Int3.inst()
    assert type_int_3.name == 'Int3'
    assert_success(type_int_3, 3)
    assert_failure(type_int_3, 5)


def test_nullable_python_object_type():
    nullable_type_bar = resolve_to_runtime_type(Optional[Bar])

    assert_type_check(nullable_type_bar.type_check(BarObj()))
    assert_type_check(nullable_type_bar.type_check(None))

    res = nullable_type_bar.type_check('not_a_bar')
    assert not res.success


def test_nullable_int_coercion():
    int_type = resolve_to_runtime_type(Int)
    assert_type_check(int_type.type_check(1))

    res = int_type.type_check(None)
    assert not res.success

    nullable_int_type = resolve_to_runtime_type(Optional[Int])
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

    list_of_int = resolve_to_runtime_type(List[Int])

    assert_failure(list_of_int, None)
    assert_success(list_of_int, [])
    assert_success(list_of_int, [1])
    assert_failure(list_of_int, [None])

    nullable_int_of_list = resolve_to_runtime_type(Optional[List[Int]])

    assert_success(nullable_int_of_list, None)
    assert_success(nullable_int_of_list, [])
    assert_success(nullable_int_of_list, [1])
    assert_failure(nullable_int_of_list, [None])

    list_of_nullable_int = resolve_to_runtime_type(List[Optional[Int]])
    assert_failure(list_of_nullable_int, None)
    assert_success(list_of_nullable_int, [])
    assert_success(list_of_nullable_int, [1])
    assert_success(list_of_nullable_int, [None])

    nullable_list_of_nullable_int = resolve_to_runtime_type(Optional[List[Optional[Int]]])
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


class ThrowsExceptionType(RuntimeType):
    def __init__(self):
        super(ThrowsExceptionType, self).__init__(
            key='ThrowsExceptionType', name='ThrowsExceptionType'
        )

    def type_check(self, value):
        raise Exception('kdjfkjd')


class BadType(RuntimeType):
    def __init__(self):
        super(BadType, self).__init__(key='BadType', name='BadType')

    def type_check(self, _value):
        return 'kdjfkjd'


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
    assert re.match(
        re.escape(
            'Type checks must return TypeCheck. Type check for type BadType returned value of '
            'type <'
        )
        + '(class|type)'
        + re.escape(' \'str\'> when checking runtime value of type <')
        + '(class|type)'
        + re.escape(' \'int\'>.'),
        type_check_data.description,
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

    assert re.match(
        re.escape(
            'Type checks must return TypeCheck. Type check for type BadType returned value of '
            'type <'
        )
        + '(class|type)'
        + re.escape(' \'str\'> when checking runtime value of type <')
        + '(class|type)'
        + re.escape(' \'int\'>.'),
        type_check_data.description,
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
    class _CustomDict(RuntimeType):
        def __init__(self):
            super(_CustomDict, self).__init__(name=name, key=name)

        def type_check(self, value):
            if not isinstance(value, dict):
                return TypeCheck(
                    False,
                    description='Value {value} should be of type {type_name}.'.format(
                        value=value, type_name=self.name
                    ),
                )
            for key in value:
                if not key in permitted_key_names:
                    return TypeCheck(
                        False,
                        description=(
                            'Key {name} is not a permitted value, values can only be of: '
                            '{name_list}'
                        ).format(name=value.name, name_list=permitted_key_names),
                    )
            return TypeCheck(
                True,
                metadata_entries=[
                    EventMetadataEntry.text(label='row_count', text=str(len(value))),
                    EventMetadataEntry.text(label='series_names', text=', '.join(value.keys())),
                ],
            )

    return _CustomDict


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
