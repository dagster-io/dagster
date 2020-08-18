import pytest
from lakehouse import AssetStorage, Lakehouse, asset_storage

from dagster import ModeDefinition, PresetDefinition


class DictStorage(AssetStorage):
    def __init__(self):
        self.the_dict = {}

    def save(self, obj, path, _resources):
        self.the_dict[path] = obj

    def load(self, _python_type, path, _resources):
        return self.the_dict[path]


@pytest.fixture
def basic_lakehouse_and_storages():
    storage1 = DictStorage()
    storage2 = DictStorage()

    @asset_storage()
    def some_storage(_):
        return storage1

    @asset_storage()
    def some_other_storage(_):
        return storage2

    dev_mode = ModeDefinition(
        name="dev", resource_defs={"storage1": some_storage, "storage2": some_other_storage},
    )
    dev_preset = PresetDefinition(name="dev", mode="dev", run_config={}, solid_selection=None)

    return (
        Lakehouse(mode_defs=[dev_mode], preset_defs=[dev_preset]),
        storage1,
        storage2,
    )


@pytest.fixture
def basic_lakehouse(basic_lakehouse_and_storages):  # pylint: disable=redefined-outer-name
    lakehouse, _, _ = basic_lakehouse_and_storages
    return lakehouse
