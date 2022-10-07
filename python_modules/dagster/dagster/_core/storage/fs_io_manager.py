import os
import pickle
from typing import Union

import dagster._check as check
from dagster._annotations import experimental
from dagster._config import Field, StringSource
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.metadata import MetadataEntry, MetadataValue
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager, io_manager
from dagster._core.storage.memoizable_io_manager import MemoizableIOManager
from dagster._utils import PICKLE_PROTOCOL, mkdir_p


@io_manager(
    config_schema={"base_dir": Field(StringSource, is_required=False)},
    description="Built-in filesystem IO manager that stores and retrieves values using pickling.",
)
def fs_io_manager(init_context):
    """Built-in filesystem IO manager that stores and retrieves values using pickling.

    Allows users to specify a base directory where all the step outputs will be stored. By
    default, step outputs will be stored in the directory specified by local_artifact_storage in
    your dagster.yaml file (which will be a temporary directory if not explicitly set).

    Serializes and deserializes output values using pickling and automatically constructs
    the filepaths for ops and assets.

    Assigns each op output to a unique filepath containing run ID, step key, and output name.
    Assigns each asset to a single filesystem path, at "<base_dir>/<asset_key>". If the asset key
    has multiple components, the final component is used as the name of the file, and the preceding
    components as parent directories under the base_dir.

    Subsequent materializations of an asset will overwrite previous materializations of that asset.
    So, with a base directory of "/my/base/path", an asset with key
    `AssetKey(["one", "two", "three"])` would be stored in a file called "three" in a directory
    with path "/my/base/path/one/two/".

    Example usage:


    1. Attach an IO manager to a set of assets using the reserved resource key ``"io_manager"``.

    .. code-block:: python

        from dagster import asset, fs_io_manager, repository, with_resources

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return df[:5]

        @repository
        def repo():
            return with_resources(
                [asset1, asset2],
                resource_defs={
                    "io_manager": fs_io_manager.configured({"base_dir": "/my/base/path"})
                },
            )
        )


    2. Specify a job-level IO manager using the reserved resource key ``"io_manager"``,
    which will set the given IO manager on all ops in a job.

    .. code-block:: python

        from dagster import fs_io_manager, job, op

        @op
        def op_a():
            # create df ...
            return df

        @op
        def op_b(df):
            return df[:5]

        @job(
            resource_defs={
                "io_manager": fs_io_manager.configured({"base_dir": "/my/base/path"})
            }
        )
        def job():
            op_b(op_a())


    3. Specify IO manager on :py:class:`Out`, which allows you to set different IO managers on
    different step outputs.

    .. code-block:: python

        from dagster import fs_io_manager, job, op, Out

        @op(out=Out(io_manager_key="my_io_manager"))
        def op_a():
            # create df ...
            return df

        @op
        def op_b(df):
            return df[:5]

        @job(resource_defs={"my_io_manager": fs_io_manager})
        def job():
            op_b(op_a())

    """
    base_dir = init_context.resource_config.get(
        "base_dir", init_context.instance.storage_directory()
    )

    return PickledObjectFilesystemIOManager(base_dir=base_dir)


class PickledObjectFilesystemIOManager(MemoizableIOManager):
    """Built-in filesystem IO manager that stores and retrieves values using pickling.

    Args:
        base_dir (Optional[str]): base directory where all the step outputs which use this object
            manager will be stored in.
    """

    def __init__(self, base_dir=None):
        self.base_dir = check.opt_str_param(base_dir, "base_dir")
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, context: Union[InputContext, OutputContext]) -> str:
        """Automatically construct filepath."""
        if context.has_asset_key:
            path = context.get_asset_identifier()
        else:
            path = context.get_identifier()

        return os.path.join(self.base_dir, *path)

    def has_output(self, context):
        filepath = self._get_path(context)

        return os.path.exists(filepath)

    def handle_output(self, context, obj):
        """Pickle the data and store the object to a file.

        This method omits the AssetMaterialization event so assets generated by it won't be tracked
        by the Asset Catalog.
        """
        check.inst_param(context, "context", OutputContext)

        filepath = self._get_path(context)

        if context.dagster_type.typing_type == type(None):
            check.invariant(
                obj is None,
                "Output had Nothing type or 'None' annotation, but handle_output received value "
                f"that was not None and was of type {type(obj)}.",
            )
            return None

        # Ensure path exists
        mkdir_p(os.path.dirname(filepath))

        with open(filepath, self.write_mode) as write_obj:
            try:
                pickle.dump(obj, write_obj, PICKLE_PROTOCOL)
            except (AttributeError, RecursionError, ImportError, pickle.PicklingError) as e:
                executor = context.step_context.pipeline_def.mode_definitions[0].executor_defs[0]

                if isinstance(e, RecursionError):
                    # if obj can't be pickled because of RecursionError then __str__() will also
                    # throw a RecursionError
                    obj_repr = f"{obj.__class__} exceeds recursion limit and"
                else:
                    obj_repr = obj.__str__()

                raise DagsterInvariantViolationError(
                    f"Object {obj_repr} is not picklable. You are currently using the "
                    f"fs_io_manager and the {executor.name}. You will need to use a different "
                    "io manager to continue using this output. For example, you can use the "
                    "mem_io_manager with the in_process_executor.\n"
                    "For more information on io managers, visit "
                    "https://docs.dagster.io/concepts/io-management/io-managers \n"
                    "For more information on executors, vist "
                    "https://docs.dagster.io/deployment/executors#overview"
                ) from e

        context.add_output_metadata({"path": MetadataValue.path(os.path.abspath(filepath))})

    def load_input(self, context):
        """Unpickle the file and Load it to a data object."""
        check.inst_param(context, "context", InputContext)

        if context.dagster_type.typing_type == type(None):
            return None

        filepath = self._get_path(context)
        context.add_input_metadata({"path": MetadataValue.path(os.path.abspath(filepath))})

        with open(filepath, self.read_mode) as read_obj:
            return pickle.load(read_obj)


class CustomPathPickledObjectFilesystemIOManager(IOManager):
    """Built-in filesystem IO managerthat stores and retrieves values using pickling and
    allow users to specify file path for outputs.

    Args:
        base_dir (Optional[str]): base directory where all the step outputs which use this object
            manager will be stored in.
    """

    def __init__(self, base_dir=None):
        self.base_dir = check.opt_str_param(base_dir, "base_dir")
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, path):
        return os.path.join(self.base_dir, path)

    def handle_output(self, context, obj):
        """Pickle the data and store the object to a custom file path.

        This method emits an AssetMaterialization event so the assets will be tracked by the
        Asset Catalog.
        """
        check.inst_param(context, "context", OutputContext)
        metadata = context.metadata
        path = check.str_param(metadata.get("path"), "metadata.path")

        filepath = self._get_path(path)

        # Ensure path exists
        mkdir_p(os.path.dirname(filepath))
        context.log.debug(f"Writing file at: {filepath}")

        with open(filepath, self.write_mode) as write_obj:
            pickle.dump(obj, write_obj, PICKLE_PROTOCOL)

        return AssetMaterialization(
            asset_key=AssetKey([context.pipeline_name, context.step_key, context.name]),
            metadata_entries=[
                MetadataEntry("path", value=MetadataValue.path(os.path.abspath(filepath)))
            ],
        )

    def load_input(self, context):
        """Unpickle the file from a given file path and Load it to a data object."""
        check.inst_param(context, "context", InputContext)
        metadata = context.upstream_output.metadata
        path = check.str_param(metadata.get("path"), "metadata.path")
        filepath = self._get_path(path)
        context.log.debug(f"Loading file from: {filepath}")

        with open(filepath, self.read_mode) as read_obj:
            return pickle.load(read_obj)


@io_manager(config_schema={"base_dir": Field(StringSource, is_required=True)})
@experimental
def custom_path_fs_io_manager(init_context):
    """Built-in IO manager that allows users to custom output file path per output definition.

    It requires users to specify a base directory where all the step output will be stored in. It
    serializes and deserializes output values (assets) using pickling and stores the pickled object
    in the user-provided file paths.

    Example usage:

    .. code-block:: python

        from dagster import custom_path_fs_io_manager, job, op

        @op(out=Out(metadata={"path": "path/to/sample_output"}))
        def sample_data(df):
            return df[:5]

        my_custom_path_fs_io_manager = custom_path_fs_io_manager.configured(
            {"base_dir": "path/to/basedir"}
        )

        @job(resource_defs={"io_manager": my_custom_path_fs_io_manager})
        def my_job():
            sample_data()

    """

    return CustomPathPickledObjectFilesystemIOManager(
        base_dir=init_context.resource_config.get("base_dir")
    )
