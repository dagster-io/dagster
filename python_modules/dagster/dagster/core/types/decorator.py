from dagster import check

from .runtime import define_python_dagster_type, register_python_type


def _decorate_as_dagster_type(
    bare_cls,
    name,
    description,
    input_hydration_config=None,
    output_materialization_config=None,
    serialization_strategy=None,
    auto_plugins=None,
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
    type_check=None,
):
    '''Decorate a Python class to turn it into a Dagster type.
    
    This is intended to make it straightforward to annotate existing business logic classes to
    make them compatible with the Dagster type system and to add any additional facilities, such
    as input schemas, that they may need to be useful in your pipelines.

    Args:
        python_type (cls): The python type to wrap as a Dagster type.
        name (Optional[str]): Name of the new Dagster type. If ``None``, the name (``__name__``) of
            the ``python_type`` will be used.
        description (Optional[str]): A user-readable description of the type.
        input_hydration_config (Optional[InputHydrationConfig]): An instance of a class that
            inherits from :py:class:`InputHydrationConfig` and can map config data to a value of
            this type. Specify this argument if you will need to shim values of this type using the
            config machinery. As a rule, you should use the
            :py:func:`@input_hydration_config <dagster.InputHydrationConfig>` decorator to construct
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
        type_check (Optional[Callable[[Any], Union[bool, TypeCheck]]]): If specified, this function
            will be called in place of the default isinstance type check. This function should
            return ``True`` if the type check succeds, ``False`` if it fails, or, if additional
            metadata should be emitted along with the type check success or failure, an instance of
            :py:class:`TypeCheck` with the ``success`` field set appropriately.

    Examples:

    .. code-block:: python

        # dagster_aws.s3.file_manager.S3FileHandle
        @dagster_type
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
        return _decorate_as_dagster_type(
            bare_cls=bare_cls,
            name=new_name,
            description=description,
            input_hydration_config=input_hydration_config,
            output_materialization_config=output_materialization_config,
            serialization_strategy=serialization_strategy,
            auto_plugins=auto_plugins,
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
    type_check=None,
):
    '''Create a Dagster type corresponding to an existing Python type.

    This function allows you to explicitly wrap existing types in a new Dagster type, and is
    especially useful when using library types (e.g., from a data processing library) that might
    require additional functionality such as input config to be useful in your pipelines.

    Args:
        python_type (cls): The python type to wrap as a Dagster type.
        name (Optional[str]): Name of the new Dagster type. If ``None``, the name (``__name__``) of
            the ``python_type`` will be used.
        description (Optional[str]): A user-readable description of the type.
        input_hydration_config (Optional[InputHydrationConfig]): An instance of a class that
            inherits from :py:class:`InputHydrationConfig` and can map config data to a value of
            this type. Specify this argument if you will need to shim values of this type using the
            config machinery. As a rule, you should use the
            :py:func:`@input_hydration_config <dagster.InputHydrationConfig>` decorator to construct
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
        type_check (Optional[Callable[[Any], Union[bool, TypeCheck]]]): If specified, this function
            will be called in place of the default isinstance type check. This function should
            return ``True`` if the type check succeds, ``False`` if it fails, or, if additional
            metadata should be emitted along with the type check success or failure, an instance of
            :py:class:`TypeCheck` with the ``success`` field set appropriately.
    
    Examples:

    .. code-block:: python

        # Partial example drawn from dagster_pandas.DataFrame

        DataFrame = as_dagster_type(
            pd.DataFrame,
            name='PandasDataFrame',
            description=\'\'\'Two-dimensional size-mutable, potentially heterogeneous
            tabular data structure with labeled axes (rows and columns).
            See http://pandas.pydata.org/\'\'\',
            input_hydration_config=dataframe_input_schema,
            output_materialization_config=dataframe_output_schema,
            type_check=df_type_check
        )

    See, e.g., ``dagster_pandas.DataFrame`` and ``dagster_pyspark.SparkRDD`` for fuller worked
    examples.
    '''

    return _decorate_as_dagster_type(
        bare_cls=check.type_param(existing_type, 'existing_type'),
        name=check.opt_str_param(name, 'name', existing_type.__name__),
        description=description,
        input_hydration_config=input_hydration_config,
        output_materialization_config=output_materialization_config,
        serialization_strategy=serialization_strategy,
        auto_plugins=auto_plugins,
        type_check=type_check,
    )
