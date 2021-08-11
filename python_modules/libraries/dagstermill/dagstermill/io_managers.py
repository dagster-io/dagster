import os
import pickle
from pathlib import Path
from typing import IO, Any, List, Optional

from dagster import check
from dagster.config.field import Field
from dagster.core.definitions.event_metadata import EventMetadataEntry
from dagster.core.definitions.events import AssetKey
from dagster.core.execution.context.input import InputContext
from dagster.core.execution.context.output import OutputContext
from dagster.core.storage.file_manager import FileHandle
from dagster.core.storage.io_manager import IOManager, io_manager
from dagster.utils import PICKLE_PROTOCOL, mkdir_p


class OutputNotebookIOManager(IOManager):
    def __init__(self, asset_key_prefix: Optional[List[str]] = None):
        self.asset_key_prefix = asset_key_prefix if asset_key_prefix else []

    def get_output_asset_key(self, context: OutputContext):
        return AssetKey([*self.asset_key_prefix, f"{context.step_key}_output_notebook"])

    def handle_output(self, context: OutputContext, obj: IO[bytes]):
        raise NotImplementedError

    def load_input(self, context: InputContext) -> Any:
        raise NotImplementedError


class LocalOutputNotebookIOManager(OutputNotebookIOManager):
    """TODO docstring

    pass output notebook as IO[bytes]
    """

    def __init__(self, base_dir: str, asset_key_prefix: Optional[List[str]] = None):
        super(LocalOutputNotebookIOManager, self).__init__(asset_key_prefix=asset_key_prefix)
        self.base_dir = base_dir
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, context: OutputContext) -> str:
        """Automatically construct filepath."""
        keys = context.get_run_scoped_output_identifier()
        return str(Path(self.base_dir, *keys).with_suffix(".ipynb"))

    def handle_output(self, context: OutputContext, obj: IO[bytes]):
        """obj: IO[bytes]"""
        check.inst_param(context, "context", OutputContext)

        # the output notebook itself is stored at output_file_path
        output_notebook_path = self._get_path(context)
        mkdir_p(os.path.dirname(output_notebook_path))
        with open(output_notebook_path, self.write_mode) as dest_file_obj:
            dest_file_obj.write(obj)
        yield EventMetadataEntry.fspath(path=output_notebook_path, label="path")

    def load_input(self, context) -> IO[bytes]:
        check.inst_param(context, "context", InputContext)
        # pass output notebook to downstream solids as File Object
        with open(self._get_path(context.upstream_output), self.read_mode) as file_obj:
            return file_obj


@io_manager(
    config_schema={
        "asset_key_prefix": Field(str, is_required=False),
        "base_dir": Field(str, is_required=False),
    },
)
def local_output_notebook_io_manager(init_context):
    """TODO docstring"""
    return LocalOutputNotebookIOManager(
        base_dir=init_context.resource_config.get(
            "base_dir", init_context.instance.storage_directory()
        ),
        asset_key_prefix=init_context.resource_config.get("asset_key_prefix", []),
    )


class OutputNotebookIOManagerBackCompact(OutputNotebookIOManager):
    """TODO docstring
    pass output notebook as FileHandle
    """

    def __init__(
        self,
        base_dir: str,
        asset_key_prefix: Optional[List[str]] = None,
    ):
        super(OutputNotebookIOManagerBackCompact, self).__init__(asset_key_prefix=asset_key_prefix)
        self.base_dir = base_dir
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, context: OutputContext) -> str:
        """Automatically construct filepath."""
        keys = context.get_run_scoped_output_identifier()

        return os.path.join(self.base_dir, *keys)

    def handle_output(self, context: OutputContext, obj: IO[bytes]):
        """obj: IO[bytes]"""
        check.inst_param(context, "context", OutputContext)

        output_file_path = self._get_path(context)
        # output notebook is saved by file_manager, same as the legacy code path
        output_notebook_file_handle = context.resources.file_manager.write(obj, ext="ipynb")

        yield EventMetadataEntry.fspath(path=output_notebook_file_handle.path_desc, label="path")

        # bc file name generated via file managers cannot be determined by output context, in order
        # to let downstream find it, we also need to persist the FileHandle to the actual output
        # notebook path at output_file_path.
        mkdir_p(os.path.dirname(output_file_path))
        context.log.debug(f"Writing {output_notebook_file_handle} at: {output_file_path}")
        with open(output_file_path, self.write_mode) as write_obj:
            pickle.dump(output_notebook_file_handle, write_obj, PICKLE_PROTOCOL)

    def load_input(self, context) -> FileHandle:
        """Unpickle the file and Load it to a data object."""
        check.inst_param(context, "context", InputContext)
        # load the FileHandle to the notebook path
        with open(self._get_path(context.upstream_output), self.read_mode) as read_obj:
            file_handle = pickle.load(read_obj)
        return file_handle


@io_manager(
    config_schema={"asset_key_prefix": Field(str, is_required=False)},
    required_resource_keys={"file_manager"},
)
def backcompact_output_notebook_io_manager(init_context):
    """TODO docstring"""
    return OutputNotebookIOManagerBackCompact(
        asset_key_prefix=init_context.resource_config.get("asset_key_prefix", []),
        base_dir=init_context.instance.storage_directory(),
    )
