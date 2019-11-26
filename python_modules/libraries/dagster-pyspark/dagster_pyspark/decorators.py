from dagster import check, solid


def pyspark_solid(
    name=None,
    description=None,
    input_defs=None,
    output_defs=None,
    config=None,
    required_resource_keys=None,
    metadata=None,
    step_metadata_fn=None,
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

        @solid(name=name.__name__, required_resource_keys=required_resource_keys)
        def new_compute_fn(context):
            return context.resources.pyspark.get_compute_fn(fn=name, solid_name=name.__name__)(
                context
            )

        return new_compute_fn

    def wrap(fn):
        name = non_local['name'] or fn.__name__

        @solid(
            name=name,
            description=description,
            input_defs=input_defs,
            output_defs=output_defs,
            config=config,
            required_resource_keys=non_local['required_resource_keys'],
            metadata=metadata,
            step_metadata_fn=step_metadata_fn,
        )
        def new_compute_fn(context):
            from .resources import PySparkResourceDefinition

            spark = check.inst(
                getattr(context.resources, pyspark_resource_key), PySparkResourceDefinition
            )

            return spark.get_compute_fn(fn, name)(context)

        return new_compute_fn

    return wrap
