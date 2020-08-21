from functools import update_wrapper

from dagster import check
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.core.definitions.config_mappable import IConfigMappable
from dagster.core.storage.file_manager import FileManager
from dagster.core.storage.intermediate_storage import IntermediateStorage
from dagster.utils.backcompat import rename_warning


class SystemStorageDefinition(IConfigMappable):
    """Defines run metadata and intermediate data storage behaviors.

    Example storage definitions are the default :py:func:`mem_system_storage`, which stores all
    intermediates and run data in memory, and :py:func:`fs_system_storage`, which stores all that
    data in the local filesystem. By default, storage definitions can be configured on a
    per-pipeline run basis by setting the ``storage.in_memory`` and ``storage.filesystem`` keys in
    pipeline run configuration respectively.

    It's possible to write additional system storage definitions, such as the
    :py:class:`dagster_aws.s3_system_storage`. Library authors can write system storages to
    support additional cloud providers, and users can write custom system storages to support their
    own infrastructure needs.

    Storage definitions can be made available to pipelines by setting the ``system_storage_defs`` on
    a :py:class:`ModeDefinition` attached to the pipeline definition. This will determine the config
    schema of the ``storage`` key in the pipeline run configuration.

    Args:
        name (str): Name of the storage mode.
        is_persistent (bool): Whether the storage is persistent in a way that can cross process/node
            boundaries. Execution with, for example, the multiprocess executor, or with
            dagster-airflow, requires a persistent storage mode.
        required_resource_keys(Set[str]): The resources that this storage needs at runtime to function.
        config_schema (Optional[ConfigSchema]): The schema for the storage's configuration schema.
            Configuration data passed in this schema will be made available to the
            ``system_storage_creation_fn`` under ``init_context.system_storage_config``.
        system_storage_creation_fn: (Callable[[InitSystemStorageContext], SystemStorageData])
            Called to construct the storage. This function should consume the init context and emit
            a :py:class:`SystemStorageData`.
        _configured_config_mapping_fn: This argument is for internal use only. Users should not
            specify this field. To preconfigure a resource, use the :py:func:`configured` API.
    """

    def __init__(
        self,
        name,
        is_persistent,
        required_resource_keys,
        config_schema=None,
        system_storage_creation_fn=None,
        _configured_config_mapping_fn=None,
    ):
        self._name = check.str_param(name, "name")
        self._is_persistent = check.bool_param(is_persistent, "is_persistent")
        self._config_schema = check_user_facing_opt_config_param(config_schema, "config_schema")
        self._system_storage_creation_fn = check.opt_callable_param(
            system_storage_creation_fn, "system_storage_creation_fn"
        )
        self._required_resource_keys = frozenset(
            check.set_param(required_resource_keys, "required_resource_keys", of_type=str)
        )
        self.__configured_config_mapping_fn = check.opt_callable_param(
            _configured_config_mapping_fn, "config_mapping_fn"
        )

    @property
    def config_field(self):
        rename_warning("config_schema", "config_field", "0.9.0")
        return self.config_schema

    @property
    def name(self):
        return self._name

    @property
    def is_persistent(self):
        return self._is_persistent

    @property
    def config_schema(self):
        return self._config_schema

    @property
    def system_storage_creation_fn(self):
        return self._system_storage_creation_fn

    @property
    def required_resource_keys(self):
        return self._required_resource_keys

    @property
    def _configured_config_mapping_fn(self):
        return self.__configured_config_mapping_fn

    def configured(self, config_or_config_fn, config_schema=None, **kwargs):
        """
        Wraps this object in an object of the same type that provides configuration to the inner
        object.

        Args:
            config_or_config_fn (Union[Any, Callable[[Any], Any]]): Either (1) Run configuration
                that fully satisfies this object's config schema or (2) A function that accepts run
                configuration and returns run configuration that fully satisfies this object's
                config schema.  In the latter case, config_schema must be specified.  When
                passing a function, it's easiest to use :py:func:`configured`.
            config_schema (ConfigSchema): If config_or_config_fn is a function, the config schema
                that its input must satisfy.
            name (Optional[str]): Name of the storage mode. If not specified, inherits the name
                of the storage mode being configured.

        Returns (SystemStorageDefinition): A configured version of this object.
        """
        name = check.opt_str_param(kwargs.get("name"), "name", self.name)
        wrapped_config_mapping_fn = self._get_wrapped_config_mapping_fn(
            config_or_config_fn, config_schema
        )

        return SystemStorageDefinition(
            name=name,
            is_persistent=self.is_persistent,
            required_resource_keys=self.required_resource_keys,
            config_schema=config_schema,
            system_storage_creation_fn=self.system_storage_creation_fn,
            _configured_config_mapping_fn=wrapped_config_mapping_fn,
        )


class SystemStorageData(object):
    """Represents an instance of system storage.

    Attributes:
        intermediate_storage (IntermediateStorage): An intermediates manager.
        file_manager (FileManager): A file manager.
    """

    def __init__(self, intermediate_storage, file_manager):
        self.intermediate_storage = check.inst_param(
            intermediate_storage, "intermediate_storage", IntermediateStorage
        )
        self.file_manager = check.inst_param(file_manager, "file_manager", FileManager)


def system_storage(required_resource_keys, name=None, is_persistent=True, config_schema=None):
    """Creates a system storage definition.

    The decorated function will be passed as the ``system_storage_creation_fn`` to a
    :py:class:`SystemStorageDefinition`.

    Args:
        name (str): The name of the system storage.
        is_persistent (bool): Does storage def persist in way that can cross process/node
            boundaries. Execution with, for example, the multiprocess executor or within
            the context of dagster-airflow require a persistent storage mode.
        required_resource_keys (Set[str]):
            The resources that this storage needs at runtime to function.
        config_schema (Optional[ConfigSchema]): The schema for the config. Configuration data available in
            `init_context.system_storage_config`.
    """

    if callable(name):
        check.invariant(is_persistent is True)
        check.invariant(config_schema is None)
        check.invariant(required_resource_keys is None)
        return _SystemStorageDecoratorCallable()(name)

    return _SystemStorageDecoratorCallable(
        name=name,
        is_persistent=is_persistent,
        config_schema=config_schema,
        required_resource_keys=required_resource_keys,
    )


class _SystemStorageDecoratorCallable(object):
    def __init__(
        self, name=None, is_persistent=True, config_schema=None, required_resource_keys=None
    ):
        self.name = check.opt_str_param(name, "name")
        self.is_persistent = check.bool_param(is_persistent, "is_persistent")
        self.config_schema = config_schema  # type check in definition
        self.required_resource_keys = required_resource_keys  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, "fn")

        if not self.name:
            self.name = fn.__name__

        storage_def = SystemStorageDefinition(
            name=self.name,
            is_persistent=self.is_persistent,
            config_schema=self.config_schema,
            system_storage_creation_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(storage_def, wrapped=fn)

        return storage_def
