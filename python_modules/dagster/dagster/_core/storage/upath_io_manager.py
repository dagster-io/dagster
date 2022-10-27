from __future__ import annotations

import inspect
from abc import abstractmethod
from typing import Any, List, Union, Dict

from upath import UPath

from dagster import (
    IOManager,
    InputContext,
    MemoizableIOManager,
    MetadataValue,
    OutputContext,
    TimeWindowPartitionsDefinition,
    AssetKey,
)
from dagster import _check as check


class UPathIOManagerBase(MemoizableIOManager):
    """
    Abstract IOManager base class compatible with local and cloud storage via `fsspec` (using `universal-pathlib`).
    What it handles for the use:
     - working with any filesystem supported by `fsspec`
     - handling loading multiple upstream asset partitions via PartitionMapping
     (returns a dictionary with mappings from partition_keys to loaded objects)
     - the `get_metadata` method can be customized to add additional metadata to the outputs
     - the `allow_missing_partitions: bool` metadata value can control
     either raising an error or skipping on missing partitions
    """

    extension: str = ""  # override in child class

    @abstractmethod
    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
        """
        Child classes should override this method to write the object to the filesystem.

        Args:
            context:
            obj:
            path:

        Returns:

        """
        ...

    @abstractmethod
    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        """
        Child classes should override this method to load the object from the filesystem.

        Args:
            context:
            path:

        Returns:

        """
        ...

    @staticmethod
    def get_metadata(context: OutputContext, obj: Any) -> Dict[str, MetadataValue]:
        """
        Child classes should override this method to add custom metadata to the outputs.

        Args:
            context:
            obj:

        Returns:

        """
        return {}

    def __init__(
        self,
        base_path: UPath,
    ):
        assert self.extension == "" or "." in self.extension

        self._base_path = base_path

    def has_output(self, context: OutputContext) -> bool:
        return self._get_path(context).exists()

    def _get_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        if context.has_asset_key:
            # we are dealing with an asset
            context_path = ["assets"] + list(context.asset_key.path)

            if context.has_asset_partitions:
                # add partition
                context_path += [context.partition_key]
        else:
            # we are dealing with an op output
            context_path = ["runs"] + list(context.get_identifier())

        return self._base_path.joinpath(*context_path).with_suffix(self.extension)

    def load_input(self, context: InputContext) -> Union[Any, Dict[str, Any]]:
        # In this load_input function, we vary the behavior based on the type of the downstream input
        # if the type is a List, we load a list of mapped partitions.
        path = self._get_path(context)
        assert context.metadata is not None
        allow_missing_partitions = context.metadata.get("allow_missing_partitions", False)

        # unfortunately, this doesn't work for Python 3.7 : inspect.get_annotations(self.serialize)["obj"]
        expected_type = inspect.signature(self.dump_to_path).parameters["obj"].annotation

        if context.dagster_type.typing_type == expected_type:
            context.log.debug(f"Loading from {path} using {self.__class__.__name__}")
            obj = self.load_from_path(context=context, path=path)
            context.add_input_metadata(
                {
                    "path": MetadataValue.path(path),
                }
            )
            return obj

        # FIXME: use a custom PartitionsDict type instead of Dict
        elif (
            hasattr(context.dagster_type.typing_type, "__origin__")
            and context.dagster_type.typing_type.__origin__ in (Dict, dict)
            and context.dagster_type.typing_type.__args__[1] == expected_type
        ):
            # load multiple partitions
            if not context.has_asset_partitions:
                raise TypeError(
                    f"Detected {context.dagster_type.typing_type} input type "
                    f"but the asset is not partitioned"
                )

            base_dir: UPath = path.parent

            partition_keys = context.asset_partition_keys

            context.log.debug(f"Loading {len(partition_keys)} partitions...")

            objs: Dict[str, Any] = {}

            for partition_key in partition_keys:
                path_with_partition = base_dir / f"{partition_key}{self.extension}"
                context.log.debug(
                    f"Loading partition from {path_with_partition} using {self.__class__.__name__}"
                )
                try:
                    obj = self.load_from_path(context=context, path=path_with_partition)
                    objs[partition_key] = obj
                except FileNotFoundError as e:
                    if not allow_missing_partitions:
                        raise e
                    context.log.debug(
                        f"Couldn't load partition {path_with_partition} and skipped it"
                    )
            return objs
        else:
            return check.failed(
                f"Inputs of type {context.dagster_type} are not supported. Expected {expected_type}. "
                f"Please specify the correct type for this input either in the op signature, "
                f"corresponding In or in the {self.__class__.__name__}.dump_to_path type annotation."
            )

    def handle_output(self, context: OutputContext, obj: Any):
        path = self._get_path(context)
        path.parent.mkdir(parents=True, exist_ok=True)
        context.log.debug(f"Saving to {path} using {self.__class__.__name__}")
        self.dump_to_path(context=context, obj=obj, path=path)

        metadata = {"path": MetadataValue.path(path)}
        custom_metadata = self.get_metadata(obj, context)
        metadata.update(custom_metadata)  # type: ignore

        context.add_output_metadata(metadata)
