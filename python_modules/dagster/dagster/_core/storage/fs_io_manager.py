import os
import pickle
from typing import TYPE_CHECKING, Any, Optional

from pydantic import Field

import dagster._check as check
from dagster import (
    DagsterInvariantViolationError,
    Field as DagsterField,
)
from dagster._annotations import experimental
from dagster._config import StringSource
from dagster._config.pythonic_config import ConfigurableIOManagerFactory
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.execution.context.init import InitResourceContext
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager, dagster_maintained_io_manager, io_manager
from dagster._core.storage.upath_io_manager import UPathIOManager
from dagster._utils import PICKLE_PROTOCOL, mkdir_p

if TYPE_CHECKING:
    from typing_extensions import Literal
    from upath import UPath


class FilesystemIOManager(ConfigurableIOManagerFactory["PickledObjectFilesystemIOManager"]):
    """Built-in filesystem IO manager that stores and retrieves values using pickling.

    The base directory that the pickle files live inside is determined by:

    * The IO manager's "base_dir" configuration value, if specified. Otherwise...
    * A "storage/" directory underneath the value for "local_artifact_storage" in your dagster.yaml
      file, if specified. Otherwise...
    * A "storage/" directory underneath the directory that the DAGSTER_HOME environment variable
      points to, if that environment variable is specified. Otherwise...
    * A temporary directory.

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

        from dagster import Definitions, asset, FilesystemIOManager

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return asset1[:5]

        defs = Definitions(
            assets=[asset1, asset2],
            resources={
                "io_manager": FilesystemIOManager(base_dir="/my/base/path")
            },
        )


    2. Specify a job-level IO manager using the reserved resource key ``"io_manager"``,
    which will set the given IO manager on all ops in a job.

    .. code-block:: python

        from dagster import FilesystemIOManager, job, op

        @op
        def op_a():
            # create df ...
            return df

        @op
        def op_b(df):
            return df[:5]

        @job(
            resource_defs={
                "io_manager": FilesystemIOManager(base_dir="/my/base/path")
            }
        )
        def job():
            op_b(op_a())


    3. Specify IO manager on :py:class:`Out`, which allows you to set different IO managers on
    different step outputs.

    .. code-block:: python

        from dagster import FilesystemIOManager, job, op, Out

        @op(out=Out(io_manager_key="my_io_manager"))
        def op_a():
            # create df ...
            return df

        @op
        def op_b(df):
            return df[:5]

        @job(resource_defs={"my_io_manager": FilesystemIOManager()})
        def job():
            op_b(op_a())

    """

    base_dir: Optional[str] = Field(default=None, description="Base directory for storing files.")

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def create_io_manager(self, context: InitResourceContext) -> "PickledObjectFilesystemIOManager":
        base_dir = self.base_dir or check.not_none(context.instance).storage_directory()
        return PickledObjectFilesystemIOManager(base_dir=base_dir)


@dagster_maintained_io_manager
@io_manager(
    config_schema=FilesystemIOManager.to_config_schema(),
    description="Built-in filesystem IO manager that stores and retrieves values using pickling.",
)
def fs_io_manager(init_context: InitResourceContext) -> "PickledObjectFilesystemIOManager":
    """Built-in filesystem IO manager that stores and retrieves values using pickling.

    The base directory that the pickle files live inside is determined by:

    * The IO manager's "base_dir" configuration value, if specified. Otherwise...
    * A "storage/" directory underneath the value for "local_artifact_storage" in your dagster.yaml
      file, if specified. Otherwise...
    * A "storage/" directory underneath the directory that the DAGSTER_HOME environment variable
      points to, if that environment variable is specified. Otherwise...
    * A temporary directory.

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

        from dagster import Definitions, asset, fs_io_manager

        @asset
        def asset1():
            # create df ...
            return df

        @asset
        def asset2(asset1):
            return asset1[:5]

        defs = Definitions(
            assets=[asset1, asset2],
            resources={
                "io_manager": fs_io_manager.configured({"base_dir": "/my/base/path"})
            },
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
    return FilesystemIOManager.from_resource_context(init_context)


class PickledObjectFilesystemIOManager(UPathIOManager):
    """Built-in filesystem IO manager that stores and retrieves values using pickling.
    Is compatible with local and remote filesystems via `universal-pathlib` and `fsspec`.
    Learn more about how to use remote filesystems here: https://github.com/fsspec/universal_pathlib.

    Args:
        base_dir (Optional[str]): base directory where all the step outputs which use this object
            manager will be stored in.
        **kwargs: additional keyword arguments for `universal_pathlib.UPath`.
    """

    extension: str = ""  # TODO: maybe change this to .pickle? Leaving blank for compatibility.

    def __init__(self, base_dir=None, **kwargs):
        from upath import UPath

        self.base_dir = check.opt_str_param(base_dir, "base_dir")

        super().__init__(base_path=UPath(base_dir, **kwargs))

    def dump_to_path(self, context: OutputContext, obj: Any, path: "UPath"):
        try:
            with path.open("wb") as file:
                pickle.dump(obj, file, PICKLE_PROTOCOL)
        except (AttributeError, RecursionError, ImportError, pickle.PicklingError) as e:
            executor = context.step_context.job_def.executor_def

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
                "https://docs.dagster.io/guides/build/io-managers/ \n"
                "For more information on executors, vist "
                "https://docs.dagster.io/guides/operate/run-executors"
            ) from e

    def load_from_path(self, context: InputContext, path: "UPath") -> Any:
        with path.open("rb") as file:
            return pickle.load(file)


class CustomPathPickledObjectFilesystemIOManager(IOManager):
    """Built-in filesystem IO managerthat stores and retrieves values using pickling and
    allow users to specify file path for outputs.

    Args:
        base_dir (Optional[str]): base directory where all the step outputs which use this object
            manager will be stored in.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = check.opt_str_param(base_dir, "base_dir")
        self.write_mode: Literal["wb"] = "wb"
        self.read_mode: Literal["rb"] = "rb"

    def _get_path(self, path: str) -> str:
        return os.path.join(self.base_dir, path)  # type: ignore  # (possible none)

    def handle_output(self, context: OutputContext, obj: object):
        """Pickle the data and store the object to a custom file path.

        This method emits an AssetMaterialization event so the assets will be tracked by the
        Asset Catalog.
        """
        check.inst_param(context, "context", OutputContext)
        metadata = context.definition_metadata
        path = check.str_param(metadata.get("path"), "metadata.path")

        filepath = self._get_path(path)

        # Ensure path exists
        mkdir_p(os.path.dirname(filepath))
        context.log.debug(f"Writing file at: {filepath}")

        with open(filepath, self.write_mode) as write_obj:
            pickle.dump(obj, write_obj, PICKLE_PROTOCOL)

        return AssetMaterialization(
            asset_key=AssetKey([context.job_name, context.step_key, context.name]),
            metadata={"path": MetadataValue.path(os.path.abspath(filepath))},
        )

    def load_input(self, context: InputContext) -> object:
        """Unpickle the file from a given file path and Load it to a data object."""
        check.inst_param(context, "context", InputContext)
        metadata = context.upstream_output.definition_metadata  # type: ignore  # (possible none)
        path = check.str_param(metadata.get("path"), "metadata.path")
        filepath = self._get_path(path)
        context.log.debug(f"Loading file from: {filepath}")

        with open(filepath, self.read_mode) as read_obj:
            return pickle.load(read_obj)


@dagster_maintained_io_manager
@io_manager(config_schema={"base_dir": DagsterField(StringSource, is_required=True)})
@experimental
def custom_path_fs_io_manager(
    init_context: InitResourceContext,
) -> CustomPathPickledObjectFilesystemIOManager:
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
