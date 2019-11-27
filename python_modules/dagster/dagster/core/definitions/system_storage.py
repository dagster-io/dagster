from functools import update_wrapper

from dagster import check
from dagster.core.storage.file_manager import FileManager
from dagster.core.storage.intermediates_manager import IntermediatesManager
from dagster.core.types.field_utils import check_user_facing_opt_field_param

from .config import resolve_config_field


class SystemStorageDefinition(object):
    '''
    Dagster stores run metadata and intermediate data on the user's behalf.
    The SystemStorageDefinition exists in order to configure and customize
    those behaviors.

    Example storage definitions are the mem_system_storage in this module,
    which stores all intermediates and run data in memory. and the fs_system_storage,
    which stores all that data in the local filesystem.

    In dagster_aws there is the S3SystemStorageDefinition. We anticipate having
    system storage for every major cloud provider. And it is user customizable
    for users with custom infrastructure needs.

    The storage definitions passed into the ModeDefinition determine the config
    schema of the "storage" section of the environment configuration.

    Args:
        name (str): Name of the storage mode.
        is_persistent (bool): Does storage def persist in a way that can cross process/node
            boundaries. Execution with, for example, the multiprocess executor or within
            the context of dagster-airflow requires a persistent storage mode.
        config_field (Field): Configuration field for its section of the storage config.
        system_storage_creation_fn: (Callable[InitSystemStorageContext, SystemStorageData])
            Called by the system. The author of the StorageSystemDefinition must provide this function,
            which consumes the init context and then emits the SystemStorageData.
        required_resource_keys(Set[str]):
            The resources that this storage needs at runtime to function.
    '''

    def __init__(
        self,
        name,
        is_persistent,
        config_field=None,
        system_storage_creation_fn=None,
        required_resource_keys=None,
    ):
        self.name = check.str_param(name, 'name')
        self.is_persistent = check.bool_param(is_persistent, 'is_persistent')
        self.config_field = check_user_facing_opt_field_param(
            config_field,
            'config_field',
            'of a SystemStorageDefinition named {name}'.format(name=self.name),
        )
        self.system_storage_creation_fn = check.opt_callable_param(
            system_storage_creation_fn, 'system_storage_creation_fn'
        )
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )


class SystemStorageData(object):
    def __init__(self, intermediates_manager, file_manager):
        self.intermediates_manager = check.inst_param(
            intermediates_manager, 'intermediates_manager', IntermediatesManager
        )
        self.file_manager = check.inst_param(file_manager, 'file_manager', FileManager)


def system_storage(
    name=None, is_persistent=True, config_field=None, config=None, required_resource_keys=None
):
    '''A decorator for creating a SystemStorageDefinition. The decorated function will be used as the
    system_storage_creation_fn in a SystemStorageDefinition.

    Args:
        name (str)
        is_persistent (bool): Does storage def persist in way that can cross process/node
            boundaries. Execution with, for example, the multiprocess executor or within
            the context of dagster-airflow require a persistent storage mode.
        required_resource_keys (Set[str]):
            The resources that this storage needs at runtime to function.
        config (Dict[str, Field]):
            The schema for the configuration data made available to the system_storage_creation_fn.
        config_field (Field):
            Used in the rare case of a top level config type other than a dictionary.

            Only one of config or config_field can be provided.

    '''

    if callable(name):
        check.invariant(is_persistent is True)
        check.invariant(config_field is None)
        check.invariant(config is None)
        check.invariant(required_resource_keys is None)
        return _SystemStorageDecoratorCallable()(name)

    return _SystemStorageDecoratorCallable(
        name=name,
        is_persistent=is_persistent,
        config_field=resolve_config_field(config_field, config, '@system_storage'),
        required_resource_keys=required_resource_keys,
    )


class _SystemStorageDecoratorCallable(object):
    def __init__(
        self, name=None, is_persistent=True, config_field=None, required_resource_keys=None
    ):
        self.name = check.opt_str_param(name, 'name')
        self.is_persistent = check.bool_param(is_persistent, 'is_persistent')
        self.config_field = config_field  # type check in definition
        self.required_resource_keys = required_resource_keys  # type check in definition

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

        if not self.name:
            self.name = fn.__name__

        storage_def = SystemStorageDefinition(
            name=self.name,
            is_persistent=self.is_persistent,
            config_field=self.config_field,
            system_storage_creation_fn=fn,
            required_resource_keys=self.required_resource_keys,
        )

        update_wrapper(storage_def, wrapped=fn)

        return storage_def
