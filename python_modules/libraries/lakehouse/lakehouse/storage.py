from abc import ABCMeta, abstractmethod
from functools import update_wrapper

import six

from dagster import ResourceDefinition, check
from dagster.core.definitions.config import is_callable_valid_config_arg


class AssetStorage(six.with_metaclass(ABCMeta)):
    """An AssetStorage describes how to save and load assets."""

    @abstractmethod
    def save(self, obj, path, resources):
        pass

    @abstractmethod
    def load(self, python_type, path, resources):
        pass


class AssetStorageDefinition(ResourceDefinition):
    def __init__(
        self,
        resource_fn=None,
        config_schema=None,
        description=None,
        _configured_config_mapping_fn=None,
        type_policies=None,
    ):
        super(AssetStorageDefinition, self).__init__(
            resource_fn=resource_fn,
            config_schema=config_schema,
            description=description,
            _configured_config_mapping_fn=_configured_config_mapping_fn,
        )
        self._type_policies = type_policies

    @property
    def type_policies(self):
        return self._type_policies


def asset_storage(config_schema=None, description=None, type_policies=None):
    first_arg = config_schema
    first_arg_is_fn = callable(config_schema) and not is_callable_valid_config_arg(config_schema)
    actual_config_schema = None if first_arg_is_fn else config_schema

    def inner(fn):
        check.callable_param(fn, "fn")

        resource_def = AssetStorageDefinition(
            resource_fn=fn,
            config_schema=actual_config_schema,
            description=description,
            type_policies=type_policies,
        )

        update_wrapper(resource_def, wrapped=fn)

        return resource_def

    if first_arg_is_fn:
        return inner(first_arg)

    return inner
