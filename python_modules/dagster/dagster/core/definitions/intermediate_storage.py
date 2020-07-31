from collections import namedtuple
from functools import update_wrapper

from dagster import check
from dagster.config.field_utils import check_user_facing_opt_config_param
from dagster.utils.backcompat import rename_warning


class IntermediateStorageDefinition(
    namedtuple(
        '_IntermediateStorageDefinition',
        'name is_persistent config_schema intermediate_storage_creation_fn required_resource_keys',
    )
):
    '''Defines intermediate data storage behaviors.
    Args:
        name (str): Name of the storage mode.
        is_persistent (bool): Whether the storage is persistent in a way that can cross process/node
            boundaries. Re-execution with, for example, the multiprocess executor, or with
            dagster-airflow, requires a persistent storage mode.
        config_schema (Optional[ConfigSchema]): The schema for the storage's configuration schema.
            Configuration data passed in this schema will be made available to the
            ``intermediate_storage_creation_fn`` under ``init_context.intermediate_storage_config``.
        intermediate_storage_creation_fn: (Callable[[InitIntermediateStorageContext], IntermediateStorage])
            Called to construct the storage. This function should consume the init context and emit
            a :py:class:`IntermediateStorage`.
        required_resource_keys(Optional[Set[str]]): The resources that this storage needs at runtime to function.
    '''

    def __new__(
        cls,
        name,
        is_persistent,
        required_resource_keys,
        config_schema=None,
        intermediate_storage_creation_fn=None,
    ):
        return super(IntermediateStorageDefinition, cls).__new__(
            cls,
            name=check.str_param(name, 'name'),
            is_persistent=check.bool_param(is_persistent, 'is_persistent'),
            config_schema=check_user_facing_opt_config_param(config_schema, 'config_schema'),
            intermediate_storage_creation_fn=check.opt_callable_param(
                intermediate_storage_creation_fn, 'intermediate_storage_creation_fn'
            ),
            required_resource_keys=frozenset(
                check.set_param(
                    required_resource_keys if required_resource_keys else set(),
                    'required_resource_keys',
                    of_type=str,
                )
            ),
        )

    @property
    def config_field(self):
        rename_warning('config_schema', 'config_field', '0.9.0')
        return self.config_schema


def intermediate_storage(
    required_resource_keys=None, name=None, is_persistent=True, config_schema=None
):
    '''Creates an intermediate storage definition

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
    '''

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


class _IntermediateStorageDecoratorCallable(object):
    def __init__(
        self, name=None, is_persistent=True, config_schema=None, required_resource_keys=None
    ):
        self.name = check.opt_str_param(name, 'name')
        self.is_persistent = check.bool_param(is_persistent, 'is_persistent')
        self.config_schema = check_user_facing_opt_config_param(config_schema, 'config_schema')
        self.required_resource_keys = check.opt_set_param(
            required_resource_keys, 'required_resource_keys', of_type=str
        )

    def __call__(self, fn):
        check.callable_param(fn, 'fn')

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
