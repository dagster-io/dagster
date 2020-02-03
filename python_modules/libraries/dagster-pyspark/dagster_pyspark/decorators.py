from functools import wraps

from dagster import check
from dagster.core.definitions.decorators import _Solid


def pyspark_solid(
    name=None,
    description=None,
    input_defs=None,
    output_defs=None,
    config=None,
    required_resource_keys=None,
    tags=None,
    pyspark_resource_key=None,
):
    # Permit the user to provide a named pyspark resource
    pyspark_resource_key = check.opt_str_param(
        pyspark_resource_key, 'pyspark_resource_key', default='pyspark'
    )

    # Expect a pyspark resource
    required_resource_keys = check.opt_set_param(required_resource_keys, 'required_resource_keys')
    required_resource_keys.add(pyspark_resource_key)

    # nonlocal keyword not available in Python 2
    non_local = {'name': name, 'required_resource_keys': required_resource_keys}

    # Handle when we're called bare without arguments (e.g. name is actually the callable, not the
    # solid name)
    if callable(name):

        @wraps(name)
        def new_compute_fn(context, *args, **kwargs):
            return context.resources.pyspark.get_compute_fn(fn=name, solid_name=name.__name__)(
                context, *args, **kwargs
            )

        # py2 compat - fixed in functools on py3
        # See: https://bugs.python.org/issue17482
        new_compute_fn.__wrapped__ = name

        return _Solid(name=name.__name__, required_resource_keys=required_resource_keys,)(
            new_compute_fn
        )

    def wrap(fn):
        name = non_local['name'] or fn.__name__

        @wraps(fn)
        def new_compute_fn(context, *args, **kwargs):
            from .resources import PySparkResourceDefinition

            spark = check.inst(
                getattr(context.resources, pyspark_resource_key), PySparkResourceDefinition
            )

            return spark.get_compute_fn(fn, name)(context, *args, **kwargs)

        # py2 compat - fixed in functools on py3
        # See: https://bugs.python.org/issue17482
        new_compute_fn.__wrapped__ = fn

        return _Solid(
            name=name,
            description=description,
            input_defs=input_defs,
            output_defs=output_defs,
            config=config,
            required_resource_keys=non_local['required_resource_keys'],
            tags=tags,
        )(new_compute_fn)

    return wrap
