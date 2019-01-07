from dagster import check

from .utils import check_valid_name


class ExpectationResult(object):
    '''
    When Expectations are evaluated in the callback passed to ExpectationDefinitions,
    the user must return an ExpectationResult object from the callback.

    Attributes:

        success (bool): Whether the expectation passed or not.
        message (str): Information about the computation. Typically only used in the failure case.
        result_context (Any): Arbitrary information about the expectation result.
    '''

    def __init__(self, success, message=None, result_context=None):
        self.success = check.bool_param(success, 'success')
        self.message = check.opt_str_param(message, 'message')
        self.result_context = check.opt_dict_param(result_context, 'result_context')


class ExpectationDefinition(object):
    '''
    Expectations represent a data quality test. It performs an arbitrary computation
    to see if a given input or output satisfies the expectation.

    Attributes:

        name (str): The name of the expectation. Names should be unique per-solid.
        expectation_fn (callable):
            This is the implementation of expectation computation. It should be a callback
            of the form.

            (context: ExecutionContext, info: ExpectationExecutionInfo, value: Any)
            : ExpectationResult

            "value" conforms to the type check performed within the Dagster type system.

            e.g. If the expectation is declare on an input of type dagster_pd.DataFrame, you can
            assume that value is a pandas.DataFrame

        description (str): Description of expectation. Optional.

    Example:

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
