from dagster import check
from dagster.core.errors import DagsterError

from .utils import check_valid_name


class DagsterIOExpectationFailedError(DagsterError):
    '''Thrown with pipeline configured to throw on expectation failure'''

    def __init__(self, expectation_context, value, *args, **kwargs):
        super(DagsterIOExpectationFailedError, self).__init__(*args, **kwargs)
        self.expectation_context = expectation_context
        self.value = value

    def __repr__(self):
        inout_def = self.expectation_context.inout_def
        return (
            'DagsterIOExpectationFailedError(solid={solid_name}, {key}={inout_name}, '
            'expectation={e_name}, value={value})'
        ).format(
            solid_name=self.expectation_context.solid.name,
            key=inout_def.descriptive_key,
            inout_name=inout_def.name,
            e_name=self.expectation_context.expectation_def.name,
            value=repr(self.value),
        )

    def __str__(self):
        return self.__repr__()


class IOExpectationDefinition(object):
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
                IOExpectationDefinition(
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
