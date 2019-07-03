import time
from functools import wraps

from dagster import DagsterInvariantViolationError, Output, SolidDefinition
from dagster.core.types.evaluator import evaluate_config
from dagster.core.types.evaluator.errors import DagsterEvaluateConfigValueError


def single_output_transform(name, input_defs, compute_fn, output_def, description=None):
    '''It is commmon to want a Solid that has only inputs, a single output (with the default
    name), and no config. So this is a helper function to do that. This compute function
    must return the naked return value (as opposed to a Output object).

    Args:
        name (str): Name of the solid.
        input_defs (List[InputDefinition]): Inputs of solid.
        compute_fn (callable):
            Callable with the signature
            (context: ExecutionContext, inputs: Dict[str, Any]) : Any
        output_def (OutputDefinition): Output of the solid.
        description (str): Descripion of the solid.

    Returns:
        SolidDefinition:

    Example:

        .. code-block:: python

            single_output_transform(
                'add_one',
                input_defs=InputDefinition('num', types.Int),
                output_def=OutputDefinition(types.Int),
                compute_fn=lambda context, inputs: inputs['num'] + 1
            )

    '''

    def _new_compute_fn(context, input_defs):
        value = compute_fn(context, input_defs)
        if isinstance(value, Output):
            raise DagsterInvariantViolationError(
                '''Single output compute Solid {name} returned a Output. Just return
                value directly without wrapping it in Output'''
            )
        yield Output(value=value)

    return SolidDefinition(
        name=name,
        input_defs=input_defs,
        compute_fn=_new_compute_fn,
        output_defs=[output_def],
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
