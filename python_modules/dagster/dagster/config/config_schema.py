class ConfigSchema(object):
    """
    ConfigSchema is a placeholder type.  Any time that it appears in documentation, it means
    that any of the following types are acceptable:

    #. A Python scalar type that resolves to a Dagster config type
       (:py:class:`~python:int`, :py:class:`~python:float`, :py:class:`~python:bool`,
       or :py:class:`~python:str`

       e.g. `@solid(config_schema=int)` or `@solid(config_schema=str)`

    #. Built-in python collections such as :py:class:`~python:list`, or :py:class:`~python:dict`).
       `list` is exactly equivalent to `Array[Any]` and `dict` is equivalent to `Permissive()`

       e.g. `@solid(config_schema=list)` or `@solid(config_schema=dict)`

    #. A Dagster config type: :py:data:`~dagster.Int`, :py:data:`~dagster.IntSource`,
       :py:data:`~dagster.Float`, :py:data:`~dagster.Bool`, :py:data:`~dagster.String`,
       :py:data:`~dagster.StringSource`, :py:data:`~dagster.Any`, :py:class:`~dagster.Array`,
       :py:data:`~dagster.Noneable`, :py:data:`~dagster.Enum`, :py:class:`~dagster.Selector`,
       :py:class:`~dagster.Shape`, or :py:class:`~dagster.Permissive`.

    #. A bare python dictionary, which will be automatically wrapped in
       :py:class:`~dagster.Shape`. Values of the dictionary are resolved recursively
       according to the same rules. E.g.

        * ``{'some_config': str}`` is equivalent to ``Shape({'some_config: str})``.

        * ``{'some_config1': {'some_config2': str}}`` is equivalent to
          ``Shape({'some_config1: Shape({'some_config2: str})})``.

    #. A bare python list of length one, whose single element will be wrapped in a
       :py:class:`~dagster.Array` is resolved recursively according to the same
       rules. E.g.

        * ``[str]`` is equivalent to ``Array[str]``.

        * ``[[str]]`` is equivalent to ``Array[Array[str]]``.

        * ``[{'some_config': str}]`` is equivalent to ``Array(Shape({'some_config: str}))``.

    #. An instance of :py:class:`~dagster.Field`.
    """

    def __init__(self):
        raise NotImplementedError(
            "ConfigSchema is a placeholder type and should not be instantiated."
        )
