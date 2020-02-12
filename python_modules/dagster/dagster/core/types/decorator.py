from dagster import check

from .dagster_type import PythonObjectDagsterType, make_python_type_usable_as_dagster_type


def usable_as_dagster_type(
    name=None,
    description=None,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
):
    '''Decorate a Python class to make it usable as a Dagster Type.
    
    This is intended to make it straightforward to annotate existing business logic classes to
    make them dagster types whose typecheck is an isinstance check against that python class. 

    Args:
        python_type (cls): The python type to make usable as python type.
        name (Optional[str]): Name of the new Dagster type. If ``None``, the name (``__name__``) of
            the ``python_type`` will be used.
        description (Optional[str]): A user-readable description of the type.
        input_hydration_config (Optional[InputHydrationConfig]): An instance of a class that
            inherits from :py:class:`InputHydrationConfig` and can map config data to a value of
            this type. Specify this argument if you will need to shim values of this type using the
            config machinery. As a rule, you should use the
            :py:func:`@input_hydration_config <dagster.input_hydration_config>` decorator to construct
            these arguments.
        output_materialization_config (Optiona[OutputMaterializationConfig]): An instance of a class
            that inherits from :py:class:`OutputMaterializationConfig` and can persist values of
            this type. As a rule, you should use the
            :py:func:`@output_materialization_config <dagster.output_materialization_config>`
            decorator to construct these arguments.
        serialization_strategy (Optional[SerializationStrategy]): An instance of a class that
            inherits from :py:class:`SerializationStrategy`. The default strategy for serializing
            this value when automatically persisting it between execution steps. You should set
            this value if the ordinary serialization machinery (e.g., pickle) will not be adequate
            for this type.
        auto_plugins (Optional[List[TypeStoragePlugin]]): If types must be serialized differently
            depending on the storage being used for intermediates, they should specify this
            argument. In these cases the serialization_strategy argument is not sufficient because
            serialization requires specialized API calls, e.g. to call an S3 API directly instead
            of using a generic file object. See ``dagster_pyspark.DataFrame`` for an example.

    Examples:

    .. code-block:: python

        # dagster_aws.s3.file_manager.S3FileHandle
        @usable_as_dagster_type
        class S3FileHandle(FileHandle):
            def __init__(self, s3_bucket, s3_key):
                self._s3_bucket = check.str_param(s3_bucket, 's3_bucket')
                self._s3_key = check.str_param(s3_key, 's3_key')

            @property
            def s3_bucket(self):
                return self._s3_bucket

            @property
            def s3_key(self):
                return self._s3_key

            @property
            def path_desc(self):
                return self.s3_path

            @property
            def s3_path(self):
                return 's3://{bucket}/{key}'.format(bucket=self.s3_bucket, key=self.s3_key)
        '''

    def _with_args(bare_cls):
        check.type_param(bare_cls, 'bare_cls')
        new_name = name if name else bare_cls.__name__

        make_python_type_usable_as_dagster_type(
            bare_cls,
            PythonObjectDagsterType(
                name=new_name,
                description=description,
                python_type=bare_cls,
                input_hydration_config=input_hydration_config,
                output_materialization_config=output_materialization_config,
                serialization_strategy=serialization_strategy,
                auto_plugins=auto_plugins,
            ),
        )
        return bare_cls

    # check for no args, no parens case
    if callable(name):
        bare_cls = name  # with no parens, name is actually the decorated class
        make_python_type_usable_as_dagster_type(
            bare_cls,
            PythonObjectDagsterType(python_type=bare_cls, name=bare_cls.__name__, description=None),
        )
        return bare_cls

    return _with_args
