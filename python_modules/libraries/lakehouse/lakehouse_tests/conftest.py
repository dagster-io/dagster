import pytest
from lakehouse import Lakehouse, TypeStoragePolicy

from dagster import ModeDefinition, PresetDefinition, resource


@pytest.fixture
def basic_lakehouse_and_storages():
    class DictStorage:
        def __init__(self):
            self.the_dict = {}

    storage1 = DictStorage()
    storage2 = DictStorage()

    @resource
    def some_storage(_):
        return storage1

    @resource
    def some_other_storage(_):
        return storage2

    dev_mode = ModeDefinition(
        name='dev', resource_defs={'storage1': some_storage, 'storage2': some_other_storage,},
    )
    dev_preset = PresetDefinition(name='dev', mode='dev', run_config={}, solid_selection=None,)

    class IntSomeStoragePolicy(TypeStoragePolicy):
        @classmethod
        def in_memory_type(cls):
            return int

        @classmethod
        def storage_definition(cls):
            return some_storage

        @classmethod
        def save(cls, obj, storage, path, _resources):
            storage.the_dict[path] = obj

        @classmethod
        def load(cls, storage, path, _resources):
            return storage.the_dict[path]

    class IntSomeOtherStoragePolicy(TypeStoragePolicy):
        @classmethod
        def in_memory_type(cls):
            return int

        @classmethod
        def storage_definition(cls):
            return some_other_storage

        @classmethod
        def save(cls, obj, storage, path, _resources):
            storage.the_dict[path] = obj

        @classmethod
        def load(cls, storage, path, _resources):
            return storage.the_dict[path]

    return (
        Lakehouse(
            mode_defs=[dev_mode],
            preset_defs=[dev_preset],
            type_storage_policies=[IntSomeStoragePolicy, IntSomeOtherStoragePolicy],
        ),
        storage1,
        storage2,
    )


@pytest.fixture
def basic_lakehouse(basic_lakehouse_and_storages):  # pylint: disable=redefined-outer-name
    lakehouse, _, _ = basic_lakehouse_and_storages
    return lakehouse
