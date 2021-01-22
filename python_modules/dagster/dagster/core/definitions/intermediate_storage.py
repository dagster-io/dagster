from functools import update_wrapper

from dagster import check
from dagster.core.definitions.configurable import AnonymousConfigurableDefinition

from .definition_config_schema import convert_user_facing_definition_config_schema
from .utils import check_valid_name


class IntermediateStorageDefinition(AnonymousConfigurableDefinition):
    """Defines intermediate data storage behaviors.

    Args:
        name (str): Name of the storage mode.
        is_persistent (bool): Whether the storage is persistent in a way that can cross process/node
            boundaries. Re-execution with, for example, the multiprocess executor, or with
            dagster-airflow, requires a persistent storage mode.
        required_resource_keys(Optional[Set[str]]): The resources that this storage needs at runtime to function.
        config_schema (Optional[ConfigSchema]): The schema for the storage's configuration schema.
            Configuration data passed in this schema will be made available to the
            ``intermediate_storage_creation_fn`` under ``init_context.intermediate_storage_config``.
        intermediate_storage_creation_fn: (Callable[[InitIntermediateStorageContext], IntermediateStorage])
            Called to construct the storage. This function should consume the init context and emit
            a :py:class:`IntermediateStorage`.
    """

    def __init__(
        self,
        name,
        is_persistent,
        required_resource_keys,
        config_schema=None,
        intermediate_storage_creation_fn=None,
        description=None,
    ):
        self._name = check_valid_name(name)
        self._is_persistent = check.bool_param(is_persistent, "is_persistent")
        self._config_schema = convert_user_facing_definition_config_schema(config_schema)
        self._intermediate_storage_creation_fn = check.opt_callable_param(
            intermediate_storage_creation_fn, "intermediate_storage_creation_fn"
        )
        self._required_resource_keys = frozenset(
            check.set_param(
                required_resource_keys if required_resource_keys else set(),
                "required_resource_keys",
                of_type=str,
            )
        )
        self._description = check.opt_str_param(description, "description")

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def is_persistent(self):
        return self._is_persistent

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def intermediate_storage_creation_fn(self):
        return self._intermediate_storage_creation_fn

    @property
    def required_resource_keys(self):
        return self._required_resource_keys

    def copy_for_configured(self, description, config_schema, _):
        return IntermediateStorageDefinition(
            name=self.name,
            is_persistent=self.is_persistent,
            required_resource_keys=self.required_resource_keys,
            config_schema=config_schema,
            intermediate_storage_creation_fn=self.intermediate_storage_creation_fn,
            description=description or self.description,
        )


def intermediate_storage(
    required_resource_keys=None, name=None, is_persistent=True, config_schema=None
):
    """Creates an intermediate storage definition

    The decorated function will be passed as the ``intermediate_storage_creation_fn`` to a
    :py:class:`IntermediateStorageDefinition`.

    Args:
        name (str): The name of the intermediate storage.
        is_persistent (bool): Whether the storage is persistent in a way that can cross process/node
            boundaries. Re-execution with, for example, the multiprocess executor, or with
            dagster-airflow, requires a persistent storage mode.
        required_resource_keys (Optional[Set[str]]):
            The resources that this storage needs at runtime to function.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.intermediate_storage_config`.
    """

    if callable(name):
        check.invariant(is_persistent is True)
        check.invariant(config_schema is None)
        check.invariant(required_resource_keys is None)
        return _IntermediateStorageDecoratorCallable()(name)

    return _IntermediateStorageDecoratorCallable(
        name=name,
        is_persistent=is_persistent,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
    )


class _IntermediateStorageDecoratorCallable:
    def __init__(
        self, name=None, is_persistent=True, config_schema=None, required_resource_keys=None
    ):
        self.name = check.opt_str_param(name, "name")
        self.is_persistent = check.bool_param(is_persistent, "is_persistent")
        self.config_schema = config_schema  # will be checked in definition
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, "required_resource_keys", of_type=str
        )

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        storage_def = IntermediateStorageDefinition(
            name=self.name,
            is_persistent=self.is_persistent,
            config_schema=self.config_schema,
            intermediate_storage_creation_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(storage_def, wrapped=fn)

        return storage_def
