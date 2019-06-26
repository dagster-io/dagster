import time
from functools import wraps

from dagster import (
    DagsterEvaluateConfigValueError,
    DagsterInvariantViolationError,
    Result,
    SolidDefinition,
)

from dagster.core.types.evaluator import evaluate_config


def single_output_transform(name, inputs, compute_fn, output, description=None):
    '''It is commmon to want a Solid that has only inputs, a single output (with the default
    name), and no config. So this is a helper function to do that. This compute function
    must return the naked return value (as opposed to a Result object).

    Args:
        name (str): Name of the solid.
        inputs (List[InputDefinition]): Inputs of solid.
        compute_fn (callable):
            Callable with the signature
            (context: ExecutionContext, inputs: Dict[str, Any]) : Any
        output (OutputDefinition): Output of the solid.
        description (str): Descripion of the solid.

    Returns:
        SolidDefinition:

    Example:

        .. code-block:: python

            single_output_transform(
                'add_one',
                inputs=InputDefinition('num', types.Int),
                output=OutputDefinition(types.Int),
                compute_fn=lambda context, inputs: inputs['num'] + 1
            )

    '''

    def _new_compute_fn(context, inputs):
        value = compute_fn(context, inputs)
        if isinstance(value, Result):
            raise DagsterInvariantViolationError(
                '''Single output compute Solid {name} returned a Result. Just return
                value directly without wrapping it in Result'''
            )
        yield Result(value=value)

    return SolidDefinition(
        name=name,
        inputs=inputs,
        compute_fn=_new_compute_fn,
        outputs=[output],
        description=description,
    )


# This is a legacy API from when the config parsing only returned a single
# error. Existing test logic was written assuming structure to this is still
# around to avoid having to port all the unit tests.
def throwing_evaluate_config_value(config_type, config_value):
    result = evaluate_config(config_type, config_value)
    if not result.success:
        raise DagsterEvaluateConfigValueError(result.errors[0].stack, result.errors[0].message)
    return result.value


def retry(ExceptionToCheck, tries=4, delay=3, backoff=2, logger=None):
    '''From:
    https://www.saltycrane.com/blog/2009/11/trying-out-retry-decorator-python/
    '''

    def deco_retry(f):
        @wraps(f)
        def f_retry(*args, **kwargs):
            mtries, mdelay = tries, delay
            while mtries > 1:
                try:
                    return f(*args, **kwargs)
                except ExceptionToCheck as e:
                    msg = "%s, Retrying in %d seconds..." % (str(e), mdelay)
                    if logger:
                        logger.warning(msg)
                    else:
                        print(msg)
                    time.sleep(mdelay)
                    mtries -= 1
                    mdelay *= backoff
            return f(*args, **kwargs)

        return f_retry  # true decorator

    return deco_retry
