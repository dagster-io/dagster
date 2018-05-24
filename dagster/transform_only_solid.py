from dagster import check
from dagster.core.definitions import (Solid, InputDefinition)


def dep_only_input(solid):
    return InputDefinition(
        name=solid.name,
        input_fn=lambda **kwargs: check.not_implemented('should not get here'),
        argument_def_dict={},
        depends_on=solid,
    )


def no_args_transform_solid(name, no_args_transform_fn, inputs=None):
    check.str_param(name, 'name')
    check.callable_param(no_args_transform_fn, 'no_args_transforn_fn')
    check.opt_list_param(inputs, 'inputs', of_type=InputDefinition)
    # check that transform should not take args?

    return Solid(
        name=name,
        inputs=inputs or [],
        transform_fn=lambda **kwargs: no_args_transform_fn(),
        outputs=[],
    )
