# # pylint: disable=W0622,W0614,W0401

from collections import namedtuple
import re

import pytest

from dagster import (
    DagsterRuntimeCoercionError,
    DagsterTypeError,
    DependencyDefinition,
    InputDefinition,
    OutputDefinition,
    PipelineDefinition,
    execute_pipeline,
    lambda_solid,
    make_dagster_type,
    solid,
)

from dagster.core.types.runtime import RuntimeType

StringTuple = make_dagster_type(namedtuple('StringTuple', 'str_one str_two'))


class SSNString(str):
    pass


class SSNStringTypeClass(RuntimeType):
    def __init__(self):
        super(SSNStringTypeClass, self).__init__(name='SSNString')

    def coerce_runtime_value(self, value):
        if isinstance(value, SSNString):
            return value

        if not isinstance(value, str):
            raise DagsterRuntimeCoercionError(
                '{value} is not a string. SSNStringType typecheck failed'.format(
                    value=repr(value)
                )
            )

        if not re.match(r'^(\d\d\d)-(\d\d)-(\d\d\d\d)$', value):
            raise DagsterRuntimeCoercionError(
                '{value} did not match SSN regex'.format(value=repr(value))
            )

        return SSNString(value)


@lambda_solid(output=OutputDefinition(StringTuple))
def produce_valid_value():
    return StringTuple(str_one='value_one', str_two='value_two')


@lambda_solid
def produce_invalid_value():
    return 'not_a_tuple'


@solid(inputs=[InputDefinition('string_tuple', StringTuple)])
def consume_string_tuple(info, string_tuple):
    info.context.info(
        'Logging value {string_tuple}'.format(string_tuple=string_tuple)
    )


@lambda_solid
def produce_valid_ssn_string():
    return '394-30-2032'


@lambda_solid
def produce_invalid_ssn_string():
    return '394-30-203239483'


@solid(inputs=[InputDefinition('ssn', SSNStringTypeClass)])
def consume_ssn(info, ssn):
    if not isinstance(ssn, SSNString):
        raise Exception('This should never be thrown')
    info.context.info('ssn: {ssn}'.format(ssn=ssn))


def define_part_twelve_step_one_pipeline():
    return PipelineDefinition(
        name='part_twelve_step_one_pipeline',
        solids=[produce_valid_value, consume_string_tuple],
        dependencies={
            'consume_string_tuple': {
                'string_tuple': DependencyDefinition('produce_valid_value')
            }
        },
    )


def define_part_twelve_step_two_pipeline():
    return PipelineDefinition(
        name='part_twelve_step_two_pipeline',
        solids=[produce_invalid_value, consume_string_tuple],
        dependencies={
            'consume_string_tuple': {
                'string_tuple': DependencyDefinition('produce_invalid_value')
            }
        },
    )


def define_part_twelve_step_three_pipeline():
    return PipelineDefinition(
        name='part_twelve_step_three_pipeline',
        solids=[produce_valid_ssn_string, consume_ssn],
        dependencies={
            'consume_ssn': {
                'ssn': DependencyDefinition('produce_valid_ssn_string')
            }
        },
    )


def define_part_twelve_step_four_pipeline():
    return PipelineDefinition(
        name='part_twelve_step_four_pipeline',
        solids=[produce_invalid_ssn_string, consume_ssn],
        dependencies={
            'consume_ssn': {
                'ssn': DependencyDefinition('produce_invalid_ssn_string')
            }
        },
    )


def test_ssn_type():
    good_ssn_string = '123-43-4939'
    good_ssn = SSNString(good_ssn_string)
    ssn_string_type = SSNStringTypeClass.inst()
    assert ssn_string_type.coerce_runtime_value(good_ssn_string) == good_ssn
    assert ssn_string_type.coerce_runtime_value(good_ssn) == good_ssn

    with pytest.raises(DagsterRuntimeCoercionError):
        ssn_string_type.coerce_runtime_value(123)

    with pytest.raises(DagsterRuntimeCoercionError):
        ssn_string_type.coerce_runtime_value(None)

    with pytest.raises(DagsterRuntimeCoercionError):
        ssn_string_type.coerce_runtime_value('12932-9234892038-384')

    with pytest.raises(DagsterRuntimeCoercionError):
        ssn_string_type.coerce_runtime_value('1292-34-383434')


def test_intro_tutorial_part_twelve_step_one():
    execute_pipeline(define_part_twelve_step_one_pipeline())


def test_intro_tutorial_part_twelve_step_two_pipeline():
    with pytest.raises(DagsterTypeError):
        execute_pipeline(define_part_twelve_step_two_pipeline())


def test_intro_tutorial_part_twelve_step_three_pipeline():
    execute_pipeline(define_part_twelve_step_three_pipeline())


def test_intro_tutorial_part_twelve_step_four():
    with pytest.raises(
        DagsterTypeError,
        match='Solid consume_ssn input ssn received value 394-30-203239483 ',
    ):
        execute_pipeline(define_part_twelve_step_four_pipeline())


if __name__ == '__main__':
    execute_pipeline(
        define_part_twelve_step_three_pipeline(), throw_on_error=True
    )
