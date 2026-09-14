import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import dagster._check as check
from dagster import (
    AssetKey,
    AssetMaterialization,
    ConfigurableIOManagerFactory,
    InitResourceContext,
    IOManager,
)
from dagster._annotations import beta
from dagster._core.definitions.metadata import MetadataValue
from dagster._core.execution.context.input import InputContext
from dagster._core.execution.context.output import OutputContext
from dagster._core.storage.io_manager import dagster_maintained_io_manager, io_manager
from dagster._utils import mkdir_p
from pydantic import Field

from dagstermill.factory import (
    SERIALIZED_ARTIFACT_HTML,
    SERIALIZED_ARTIFACT_NOTEBOOK,
    SERIALIZED_ARTIFACT_TYPE_METADATA_KEY,
    _clean_path_for_windows,
)

_SERIALIZED_ARTIFACT_EXTENSION_BY_TYPE = {
    SERIALIZED_ARTIFACT_NOTEBOOK: ".ipynb",
    SERIALIZED_ARTIFACT_HTML: ".html",
}
_SERIALIZED_ARTIFACT_METADATA_LABEL_BY_TYPE = {
    SERIALIZED_ARTIFACT_NOTEBOOK: "Executed notebook",
    SERIALIZED_ARTIFACT_HTML: "Rendered notebook",
}


class OutputNotebookIOManager(IOManager):
    def __init__(self, asset_key_prefix: Sequence[str] | None = None):
        self.asset_key_prefix = asset_key_prefix if asset_key_prefix else []

    def handle_output(self, context: OutputContext, obj: bytes):
        raise NotImplementedError

    def load_input(self, context: InputContext) -> Any:
        raise NotImplementedError


class LocalOutputNotebookIOManager(OutputNotebookIOManager):
    def __init__(self, base_dir: str, asset_key_prefix: Sequence[str] | None = None):
        super().__init__(asset_key_prefix=asset_key_prefix)
        self.base_dir = base_dir
        self.write_mode = "wb"
        self.read_mode = "rb"

    def _get_path(self, context: OutputContext, extension: str = ".ipynb") -> str:
        """Automatically construct filepath."""
        if context.has_asset_key:
            keys = context.get_asset_identifier()
        else:
            keys = context.get_run_scoped_output_identifier()
        return str(Path(self.base_dir, *keys).with_suffix(extension))

    def _get_serialized_artifact_type(self, context: OutputContext) -> str:
        serialized_artifact_type = context.output_metadata.get(
            SERIALIZED_ARTIFACT_TYPE_METADATA_KEY, SERIALIZED_ARTIFACT_NOTEBOOK
        )
        if isinstance(serialized_artifact_type, MetadataValue):
            serialized_artifact_type = serialized_artifact_type.value
        check.invariant(
            isinstance(serialized_artifact_type, str)
            and serialized_artifact_type in _SERIALIZED_ARTIFACT_EXTENSION_BY_TYPE,
            f"Unexpected dagstermill artifact type '{serialized_artifact_type}'.",
        )
        return serialized_artifact_type

    def _get_metadata(self, path: str, serialized_artifact_type: str) -> dict[str, MetadataValue]:
        normalized_path = _clean_path_for_windows(path)
        label = _SERIALIZED_ARTIFACT_METADATA_LABEL_BY_TYPE[serialized_artifact_type]
        if serialized_artifact_type == SERIALIZED_ARTIFACT_NOTEBOOK:
            return {label: MetadataValue.notebook(normalized_path)}

        return {label: MetadataValue.path(normalized_path)}

    def handle_output(self, context: OutputContext, obj: bytes):
        """obj: bytes."""
        check.inst_param(context, "context", OutputContext)

        # the output notebook itself is stored at output_file_path
        serialized_artifact_type = self._get_serialized_artifact_type(context)
        output_notebook_path = self._get_path(
            context, _SERIALIZED_ARTIFACT_EXTENSION_BY_TYPE[serialized_artifact_type]
        )
        mkdir_p(os.path.dirname(output_notebook_path))
        with open(output_notebook_path, self.write_mode) as dest_file_obj:
            dest_file_obj.write(obj)

        metadata = self._get_metadata(output_notebook_path, serialized_artifact_type)

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
        serialized_artifact_type = self._get_serialized_artifact_type(output_context)
        extension = _SERIALIZED_ARTIFACT_EXTENSION_BY_TYPE[serialized_artifact_type]
        with open(self._get_path(output_context, extension), self.read_mode) as file_obj:
            return file_obj.read()


@beta
class ConfigurableLocalOutputNotebookIOManager(ConfigurableIOManagerFactory):
    """Built-in IO Manager for handling output notebook."""

    base_dir: str | None = Field(
        default=None,
        description=(
            "Base directory to use for output notebooks. Defaults to the Dagster instance storage"
            " directory if not provided."
        ),
    )
    asset_key_prefix: list[str] = Field(
        default=[],
        description=(
            "Asset key prefix to apply to assets materialized for output notebooks. Defaults to no"
            " prefix."
        ),
    )

    @classmethod
    def _is_dagster_maintained(cls) -> bool:
        return True

    def create_io_manager(self, context: InitResourceContext) -> "LocalOutputNotebookIOManager":
        return LocalOutputNotebookIOManager(
            base_dir=self.base_dir or check.not_none(context.instance).storage_directory(),
            asset_key_prefix=self.asset_key_prefix,
        )


@beta
@dagster_maintained_io_manager
@io_manager(config_schema=ConfigurableLocalOutputNotebookIOManager.to_config_schema())
def local_output_notebook_io_manager(init_context) -> LocalOutputNotebookIOManager:
    """Built-in IO Manager that handles output notebooks."""
    return ConfigurableLocalOutputNotebookIOManager.from_resource_context(init_context)
