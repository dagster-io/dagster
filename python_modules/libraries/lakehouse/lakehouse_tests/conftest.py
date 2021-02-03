import pytest
from dagster import ModeDefinition, PresetDefinition, resource
from lakehouse import AssetStorage, Lakehouse, computed_asset


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

    @resource()
    def some_storage(_):
        return storage1

    @resource()
    def some_other_storage(_):
        return storage2

    dev_mode = ModeDefinition(
        name="dev",
        resource_defs={"storage1": some_storage, "storage2": some_other_storage},
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


@pytest.fixture
def basic_lakehouse_single_asset_pipeline(basic_lakehouse):  # pylint: disable=redefined-outer-name
    @computed_asset(storage_key="storage1", path=("apple", "banana"))
    def return_one_asset() -> int:
        return 1

    return basic_lakehouse.build_pipeline_definition("some_pipeline", [return_one_asset])
