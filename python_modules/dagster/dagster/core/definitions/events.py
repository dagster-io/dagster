from collections import namedtuple

from dagster import check

from .utils import DEFAULT_OUTPUT


class Result(namedtuple('_Result', 'value output_name')):
    '''A solid compute function return a stream of Result objects.
    An implementator of a SolidDefinition must provide a compute that
    yields objects of this type.

    Attributes:
        value (Any): Value returned by the transform.
        output_name (str): Name of the output returns. defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(cls, value, check.str_param(output_name, 'output_name'))


class Materialization(namedtuple('_Materialization', 'path name description result_metadata')):
    '''A value materialized by an execution step.

    Attributes:
        path (str): The path to the materialized value.
        name (str): A short display name for the materialized value.
        description (str): A longer description of the materialized value.
        result_metadata (dict): Arbitrary metadata about the materialized value.
    '''

    def __new__(cls, path, name=None, description=None, result_metadata=None):
        return super(Materialization, cls).__new__(
            cls,
            path=check.str_param(path, 'path'),
            name=check.opt_str_param(name, 'name'),
            description=check.opt_str_param(description, 'description'),
            result_metadata=check.opt_dict_param(result_metadata, 'result_metadata'),
        )


class ExpectationResult(namedtuple('_ExpectationResult', 'success name message result_metadata')):
    ''' Result of an expectation callback.

    When Expectations are evaluated in the callback passed to ExpectationDefinitions,
    the user must return an ExpectationResult object from the callback.

    Attributes:

        success (bool): Whether the expectation passed or not.
        name (str): Short display name for expectation
        message (str): Information about the computation. Typically only used in the failure case.
        result_metadata (dict): Arbitrary information about the expectation result.
    '''

    def __new__(cls, success, name=None, message=None, result_metadata=None):
        return super(ExpectationResult, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            name=check.opt_str_param(name, 'name'),
            message=check.opt_str_param(message, 'message'),
            result_metadata=check.opt_dict_param(result_metadata, 'result_metadata'),
        )
