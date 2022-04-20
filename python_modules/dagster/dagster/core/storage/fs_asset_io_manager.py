import os

from dagster.config import Field
from dagster.config.source import StringSource
from dagster.core.storage.io_manager import io_manager

from .fs_io_manager import PickledObjectFilesystemIOManager


@io_manager(config_schema={"base_dir": Field(StringSource, is_required=False)})
def fs_asset_io_manager(init_context):
    """IO manager that stores values on the local filesystem, serializing them with pickle.

    Each asset is assigned to a single filesystem path, at "<base_dir>/<asset_key>". If the asset
    key has multiple components, the final component is used as the name of the file, and the
    preceding components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.

    If not provided via configuration, the base dir is the local_artifact_storage in your
    dagster.yaml file. That will be a temporary directory if not explicitly set.

    So, with a base directory of "/my/base/path", an asset with key
    `AssetKey(["one", "two", "three"])` would be stored in a file called "three" in a directory
    with path "/my/base/path/one/two/".

    Example usage:

    1. Specify a collection-level IO manager using the reserved resource key ``"io_manager"``,
    which will set the given IO manager on all assets in the collection.

    .. code-block:: python

        from dagster import AssetGroup, asset, fs_asset_io_manager

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return df[:5]

        asset_group = AssetGroup(
            [asset1, asset2],
            resource_defs={
                "io_manager": fs_asset_io_manager.configured({"base_path": "/my/base/path"})
            },
        )

    2. Specify IO manager on the asset, which allows the user to set different IO managers on
    different assets.

    .. code-block:: python

        from dagster import fs_io_manager, job, op, Out

        @asset(io_manager_key="my_io_manager")
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return df[:5]

        asset_group = AssetGroup(
            [asset1, asset2],
            resource_defs={
                "my_io_manager": fs_asset_io_manager.configured({"base_path": "/my/base/path"})
            },
        )
    """
    base_dir = init_context.resource_config.get(
        "base_dir", init_context.instance.storage_directory()
    )

    return AssetPickledObjectFilesystemIOManager(base_dir=base_dir)


class AssetPickledObjectFilesystemIOManager(PickledObjectFilesystemIOManager):
    def _get_path(self, context):
        return os.path.join(self.base_dir, *context.get_asset_output_identifier())
