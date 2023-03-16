import os
from pathlib import Path
from typing import Any, List, Optional, Sequence, Union

import dagster._check as check
from dagster import AssetKey, AssetMaterialization, ConfigurableIOManager
from dagster._config import Field
from dagster._config.structured_config import infer_schema_from_config_class
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import IOManager, io_manager
from dagster._utils import mkdir_p

from dagstermill.factory import _clean_path_for_windows
from pydantic import Field as PyField


class OutputNotebookIOManager(ConfigurableIOManager):
    asset_key_prefix: List[str] = PyField([])

    def handle_output(self, context: OutputContext, obj: bytes):
        raise NotImplementedError

    def load_input(self, context: InputContext) -> Any:
        raise NotImplementedError


WRITE_MODE = "wb"
READ_MODE = "rb"


class LocalOutputNotebookIOManager(OutputNotebookIOManager):
    """Built-in IO Manager for handling output notebook."""

    base_dir: Optional[str] = PyField(None)

    def create_io_manager(self, context) -> "LocalOutputNotebookIOManager":
        config = dict(self._as_config_dict())
        config["base_dir"] = config.get("base_dir") or context.instance.storage_directory()
        return self.__class__(**config)

    @property
    def effective_base_dir(self) -> str:
        assert self.base_dir, "base_dir must be set"
        return self.base_dir

    def _get_path(self, context: OutputContext) -> str:
        """Automatically construct filepath."""
        if context.has_asset_key:
            keys = context.get_asset_identifier()
        else:
            keys = context.get_run_scoped_output_identifier()
        return str(Path(self.effective_base_dir, *keys).with_suffix(".ipynb"))

    def handle_output(self, context: OutputContext, obj: bytes):
        """obj: bytes."""
        check.inst_param(context, "context", OutputContext)

        # the output notebook itself is stored at output_file_path
        output_notebook_path = self._get_path(context)
        mkdir_p(os.path.dirname(output_notebook_path))
        with open(output_notebook_path, WRITE_MODE) as dest_file_obj:
            dest_file_obj.write(obj)

        metadata = {
            "Executed notebook": MetadataValue.notebook(
                _clean_path_for_windows(output_notebook_path)
            )
        }

        if context.has_asset_key:
            context.add_output_metadata(metadata)
        else:
            context.log_event(
                AssetMaterialization(
                    asset_key=AssetKey(
                        [*self.asset_key_prefix, f"{context.step_key}_output_notebook"]
                    ),
                    metadata=metadata,
                )
            )

    def load_input(self, context: InputContext) -> bytes:
        check.inst_param(context, "context", InputContext)
        # pass output notebook to downstream ops as File Object
        output_context = check.not_none(context.upstream_output)
        with open(self._get_path(output_context), READ_MODE) as file_obj:
            return file_obj.read()


@io_manager(config_schema=infer_schema_from_config_class(LocalOutputNotebookIOManager))
def local_output_notebook_io_manager(init_context) -> LocalOutputNotebookIOManager:
    """Built-in IO Manager that handles output notebooks."""
    return LocalOutputNotebookIOManager(
        base_dir=init_context.resource_config.get(
            "base_dir", init_context.instance.storage_directory()
        ),
        asset_key_prefix=init_context.resource_config.get("asset_key_prefix", []),
    )
