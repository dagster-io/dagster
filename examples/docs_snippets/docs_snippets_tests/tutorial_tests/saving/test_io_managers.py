from dagster import (
    AssetKey,
)
from docs_snippets.tutorial.saving import (
    add_db_io_manager,
    add_fs_io_manager,
    assets,
)


def test_fs_io_manager_can_load():
    repository = add_fs_io_manager.defs.get_repository_def()
    resource_keys = repository.get_resource_key_mapping().values()
    assert len(resource_keys) == 1
    assert "io_manager" in resource_keys


def test_db_io_manager_can_load():
    repository = add_db_io_manager.defs.get_repository_def()
    resource_keys = repository.get_resource_key_mapping().values()
    assert len(resource_keys) == 2
    assert "io_manager" in resource_keys
    assert "database_io_manager" in resource_keys


def test_asset_io_manager_binding():
    topstories = assets.topstories

    assert "database_io_manager" in topstories.required_resource_keys
    assert "database_io_manager" == topstories.get_io_manager_key_for_asset_key(
        AssetKey(["topstories"])
    )
