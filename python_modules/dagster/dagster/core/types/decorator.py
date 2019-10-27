from dagster import check

from .mapping import register_python_type
from .runtime import PYTHON_DAGSTER_TYPE_ARGS_DOCSTRING, define_python_dagster_type


def _decorate_as_dagster_type(
    bare_cls,
    name,
    description,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
    typecheck_metadata_fn=None,
    type_check=None,
):
    dagster_type_cls = define_python_dagster_type(
        name=name,
        description=description,
        python_type=bare_cls,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
        typecheck_metadata_fn=typecheck_metadata_fn,
        type_check=type_check,
    )

    register_python_type(bare_cls, dagster_type_cls)

    return bare_cls


def dagster_type(
    name=None,
    description=None,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
    typecheck_metadata_fn=None,
    type_check=None,
):
    '''
    Decorator version of as_dagster_type.
    
    This allows for the straightforward creation of your own classes for use in your
    business logic, and then annotating them to make those same classes compatible with
    the dagster type system.

    e.g.:
        .. code-block:: python

            # You have created an object for your own purposes within your app
            class MyDataObject:
                pass


    Now you want to be able to mark this as an input or output to solid. Without
    modification, this does not work.

    You must decorate it:
        .. code-block:: python

            @dagster_type
            class MyDataObject:
                pass

    Now one can using this as an input or an output into a solid.

        .. code-block:: python

            @lambda_solid
            def create_myobject() -> MyDataObject:
                return MyDataObject()

    And it is viewable in dagit and so forth, and you can use the dagster type system
    for configuration, serialization, and metadata emission.

    {args_docstring}
    '''.format(
        args_docstring=PYTHON_DAGSTER_TYPE_ARGS_DOCSTRING
    )

    def _with_args(bare_cls):
        check.type_param(bare_cls, 'bare_cls')
        new_name = name if name else bare_cls.__name__
        return _decorate_as_dagster_type(
            bare_cls=bare_cls,
            name=new_name,
            description=description,
            input_hydration_config=input_hydration_config,
            output_materialization_config=output_materialization_config,
            serialization_strategy=serialization_strategy,
            auto_plugins=auto_plugins,
            typecheck_metadata_fn=typecheck_metadata_fn,
            type_check=type_check,
        )

    # check for no args, no parens case
    if callable(name):
        klass = name  # with no parens, name is actually the decorated class
        return _decorate_as_dagster_type(bare_cls=klass, name=klass.__name__, description=None)

    return _with_args


def as_dagster_type(
    existing_type,
    name=None,
    description=None,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
    typecheck_metadata_fn=None,
    type_check=None,
):
    '''
    See documentation for :py:func:`define_python_dagster_type` for parameters.

    Takes a python cls and creates a type for it in the Dagster domain.

    Frequently you want to import a data processing library and use its types
    directly in solid definitions. To support this dagster has this facility
    that allows one to annotate *existing* classes as dagster type.

    from existing_library import FancyDataType as ExistingFancyDataType

    FancyDataType = as_dagster_type(existing_type=ExistingFancyDataType, name='FancyDataType')

    While one *could* use the existing type directly from the original library, we would
    recommend using the object returned by as_dagster_type to avoid an import-order-based bugs.

    See dagster_pandas for an example of how to do this.

    {args_docstring}
    '''.format(
        args_docstring=PYTHON_DAGSTER_TYPE_ARGS_DOCSTRING
    )

    return _decorate_as_dagster_type(
        bare_cls=check.type_param(existing_type, 'existing_type'),
        name=check.opt_str_param(name, 'name', existing_type.__name__),
        description=description,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
        typecheck_metadata_fn=typecheck_metadata_fn,
        type_check=type_check,
    )
