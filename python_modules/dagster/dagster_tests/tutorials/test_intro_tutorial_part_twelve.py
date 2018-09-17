# pylint: disable=W0622,W0614,W0401
from collections import namedtuple
import re

import pytest

from dagster import *

StringTuple = namedtuple('StringTuple', 'str_one str_two')

StringTupleType = types.PythonObjectType(
    'StringTuple',
    python_type=StringTuple,
    description='A tuple of strings.',
)

SSNString = namedtuple('SSNString', 'value')


class SSNStringTypeClass(types.DagsterType):
    def __init__(self):
        super(SSNStringTypeClass, self).__init__(name='SSNString')

    def evaluate_value(self, value):
        if isinstance(value, SSNString):
            return value

        if not isinstance(value, str):
            raise DagsterEvaluateValueError(
                '{value} is not a string. SSNStringType typecheck failed'.format(value=repr(value))
            )

        if not re.match(r'^(\d\d\d)-(\d\d)-(\d\d\d\d)$', value):
            raise DagsterEvaluateValueError(
                '{value} did not match SSN regex'.format(value=repr(value))
            )

        return SSNString(value)


SSNStringType = SSNStringTypeClass()


@lambda_solid
def produce_valid_value():
    return StringTuple(str_one='value_one', str_two='value_two')


@lambda_solid
def produce_invalid_value():
    return 'not_a_tuple'


@solid(inputs=[InputDefinition('string_tuple', StringTupleType)])
def consume_string_tuple(info, string_tuple):
    info.context.info('Logging value {string_tuple}'.format(string_tuple=string_tuple))


@lambda_solid
def produce_valid_ssn_string():
    return '394-30-2032'


@lambda_solid
def produce_invalid_ssn_string():
    return '394-30-203239483'


@solid(inputs=[InputDefinition('ssn', SSNStringType)])
def consume_ssn(info, ssn):
    info.context.info('ssn: {ssn}'.format(ssn=ssn))


def define_part_twelve_step_one():
    return PipelineDefinition(
        name='part_twelve_step_one',
        solids=[produce_valid_value, consume_string_tuple],
        dependencies={
            'consume_string_tuple': {
                'string_tuple': DependencyDefinition('produce_valid_value')
            }
        },
    )


def define_part_twelve_step_two():
    return PipelineDefinition(
        name='part_twelve_step_two',
        solids=[produce_invalid_value, consume_string_tuple],
        dependencies={
            'consume_string_tuple': {
                'string_tuple': DependencyDefinition('produce_invalid_value')
            }
        },
    )


def define_part_twelve_step_three():
    return PipelineDefinition(
        name='part_twelve_step_three',
        solids=[produce_valid_ssn_string, consume_ssn],
        dependencies={'consume_ssn': {
            'ssn': DependencyDefinition('produce_valid_ssn_string')
        }},
    )


def define_part_twelve_step_four():
    return PipelineDefinition(
        name='part_twelve_step_four',
        solids=[produce_invalid_ssn_string, consume_ssn],
        dependencies={'consume_ssn': {
            'ssn': DependencyDefinition('produce_invalid_ssn_string')
        }},
    )


def test_ssn_type():
    good_ssn_string = '123-43-4939'
    good_ssn = SSNString(good_ssn_string)
    assert SSNStringType.evaluate_value(good_ssn_string) == good_ssn
    assert SSNStringType.evaluate_value(good_ssn) == good_ssn

    with pytest.raises(DagsterEvaluateValueError):
        SSNStringType.evaluate_value(123)

    with pytest.raises(DagsterEvaluateValueError):
        SSNStringType.evaluate_value(None)

    with pytest.raises(DagsterEvaluateValueError):
        SSNStringType.evaluate_value('12932-9234892038-384')

    with pytest.raises(DagsterEvaluateValueError):
        SSNStringType.evaluate_value('1292-34-383434')


def test_intro_tutorial_part_twelve_step_one():
    execute_pipeline(define_part_twelve_step_one())


def test_intro_tutorial_part_twelve_step_two():
    with pytest.raises(DagsterTypeError):
        execute_pipeline(define_part_twelve_step_two())


def test_intro_tutorial_part_twelve_step_three():
    execute_pipeline(define_part_twelve_step_three())


def test_intro_tutorial_part_twelve_step_four():
    with pytest.raises(
        DagsterTypeError,
        match='Solid consume_ssn input ssn received value 394-30-203239483 ',
    ):
        execute_pipeline(define_part_twelve_step_four())


if __name__ == '__main__':
    execute_pipeline(define_part_twelve_step_four(), throw_on_error=True)
