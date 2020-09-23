from typing import Dict, Type

from dagster import ResourceDefinition, check, resource

from .storage import AssetStorage


class MultiTypeAssetStorage(AssetStorage):
    def __init__(self, type_storages: Dict[Type, AssetStorage]):
        self._type_storages = type_storages

    def save(self, obj, path, resources):
        self._storage_for_type(type(obj)).save(obj, path, resources)

    def load(self, python_type, path, resources):
        return self._storage_for_type(python_type).load(python_type, path, resources)

    def _storage_for_type(self, python_type):
        self.check_has_policy(python_type)
        return self._storages_for_type(python_type)[0]

    def _storages_for_type(self, python_type):
        return [
            policy
            for type_, policy in self._type_storages.items()
            if issubclass(python_type, type_)
        ]

    def check_has_policy(self, in_memory_type):
        matching_policies = self._storages_for_type(in_memory_type)
        check.invariant(
            matching_policies,
            "Missing storage for in-memory type {in_memory_type}. "
            "Supported types: {supported_types}.".format(
                in_memory_type=in_memory_type,
                supported_types=list(map(str, self._type_storages.keys())),
            ),
        )
        check.invariant(
            len(matching_policies) < 2,
            "Multiple matching storages for in-memory type {in_memory_type} ".format(
                in_memory_type=in_memory_type
            ),
        )


def multi_type_asset_storage(
    config_schema, type_storage_defs: Dict[Type, ResourceDefinition]
) -> MultiTypeAssetStorage:
    @resource(config_schema=config_schema)
    def result(init_context):
        type_storages = {
            type_: storage_def.resource_fn(init_context)
            for type_, storage_def in type_storage_defs.items()
        }
        for storage in type_storages.values():
            check.invariant(
                isinstance(storage, AssetStorage),
                "Storages within multi-type asset storages must be AssetStorages",
            )
        return MultiTypeAssetStorage(type_storages)

    return result
