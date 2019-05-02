from collections import namedtuple
from dagster import check

from .utils import check_valid_name


class ExpectationResult(namedtuple('_ExpectationResult', 'success message result_metadata')):
    ''' Result of an expectation callback.

    When Expectations are evaluated in the callback passed to ExpectationDefinitions,
    the user must return an ExpectationResult object from the callback.

    Attributes:

        success (bool): Whether the expectation passed or not.
        message (str): Information about the computation. Typically only used in the failure case.
        result_metadata (dict): Arbitrary information about the expectation result.
    '''

    def __new__(cls, success, message=None, result_metadata=None):
        return super(ExpectationResult, cls).__new__(
            cls,
            success=check.bool_param(success, 'success'),
            message=check.opt_str_param(message, 'message'),
            result_metadata=check.opt_dict_param(result_metadata, 'result_metadata'),
        )


class ExpectationDefinition(object):
    '''
    Expectations represent a data quality test. It performs an arbitrary computation
    to see if a given input or output satisfies the expectation.

    Attributes:

        name (str): The name of the expectation. Names should be unique per-solid.
        expectation_fn (callable):
            This is the implementation of an expectation computation. It should be a callback
            with the signature (**context**: `ExecutionContext`, **info**:
            `ExpectationExecutionInfo`, **value**: `Any`) : `ExpectationResult`.

            "value" conforms to the type check performed within the Dagster type system.

            e.g. If the expectation is declared on an input of type ``dagster_pandas.DataFrame``,
            you can assume that value is a ``pandas.DataFrame``.

        description (str): Description of expectation. Optional.

    Examples:

        .. code-block:: python

            InputDefinition('some_input', types.Int, expectations=[
                ExpectationDefinition(
                    name='is_positive',
                    expectation_fn=lambda(
                        _info,
                        value,
                    ): ExpectationResult(success=value > 0),
                )
            ])
    '''

    def __init__(self, name, expectation_fn, description=None):
        self.name = check_valid_name(name)
        self.expectation_fn = check.callable_param(expectation_fn, 'expectation_fn')
        self.description = check.opt_str_param(description, 'description')
