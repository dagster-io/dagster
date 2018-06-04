from dagster import check
from dagster.core.definitions import (
    Solid, InputDefinition, create_single_source_input, create_no_materialization_output
)
from dagster.utils import make_context_arg_optional


def no_args_transform_solid(name, no_args_transform_fn, inputs=None):
    check.str_param(name, 'name')
    check.callable_param(no_args_transform_fn, 'no_args_transforn_fn')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)
    # check that transform should not take args?

    true_fn = make_context_arg_optional(no_args_transform_fn)

    return Solid(
        name=name,
        inputs=inputs or [],
        transform_fn=lambda context, **kwargs: true_fn(context=context),
        output=create_no_materialization_output(),
    )
