from __future__ import annotations

import inspect
from abc import abstractmethod
from typing import Any, List

from upath import UPath

from dagster import (
    IOManager,
    InputContext,
    MemoizableIOManager,
    MetadataValue,
    OutputContext,
    TimeWindowPartitionsDefinition,
)
from dagster import _check as check


class UPathIOManagerBase(MemoizableIOManager):
    """
    Abstract IOManager base class compatible with local and cloud storage via `fsspec` (using `universal-pathlib`).
    """

    extension: str = ""  # override in child class

    def __init__(
        self,
        base_path: UPath,
    ):
        assert self.extension == "" or "." in self.extension

        self._base_path = base_path

    def has_output(self, context: OutputContext) -> bool:
        return self.get_path(context).exists()

    @abstractmethod
    def serialize(self, obj: Any, path: UPath, context: OutputContext):
        """
        Child classes should override this method.
        :param obj:
        :param path:
        :return:
        """
        ...

    @abstractmethod
    def deserialize(self, path: UPath, context: InputContext) -> Any:
        """
        Child classes should override this method.
        The `context` argument can be used to control the IOManager behavior (via `context.metadata`).
        :param path:
        :param context:
        :return:
        """
        ...

    @staticmethod
    def get_metadata(obj: Any, context: OutputContext) -> dict[str, MetadataValue]:
        """
        Child classes should override this method to add custom metadata to the outputs.
        :param obj:
        :param context:
        :return:
        """
        return {}

    def get_path(self, context: InputContext | OutputContext) -> UPath:
        if context.has_asset_key:
            # we are dealing with an asset
            # filesystem-friendly string that is scoped to the start/end times of the data slice
            context_path = ["assets"] + list(context.asset_key.path)

            if context.has_asset_partitions:
                # add partition
                context_path = context_path + [context.asset_partition_key_range.start]

        else:
            # we are dealing with op output
            context_path = ["runs"] + list(context.get_identifier())

        return self._base_path.joinpath(*context_path).with_suffix(self.extension)

    def load_input(self, context: InputContext) -> Any | list[Any]:
        # In this load_input function, we vary the behavior based on the type of the downstream input
        # if the type is a List, we load a list of mapped partitions.
        path = self.get_path(context)
        assert context.metadata is not None
        allow_missing_partitions = context.metadata.get("allow_missing_partitions", False)

        # unfortunately, this doesn't work for Python 3.7 : inspect.get_annotations(self.serialize)["obj"]
        expected_type = inspect.signature(self.serialize).parameters["obj"].annotation

        # FIXME: use a custom PartitionsList type instead of List
        if context.dagster_type.typing_type.__origin__ in (List, list) and issubclass(
            context.dagster_type.typing_type.__args__[0], expected_type
        ):
            # load multiple partitions
            if not context.has_asset_partitions:
                raise TypeError(
                    f"Detected {context.dagster_type.typing_type} input type "
                    f"but the asset is not partitioned"
                )

            base_dir: UPath = path.parent

            # access the mapped partitions of the upstream asset
            # this should be simplified in the future
            partitions_def = context.asset_partitions_def
            assert partitions_def is not None
            assert isinstance(partitions_def, TimeWindowPartitionsDefinition)
            partitions = partitions_def.get_partition_keys_in_range(
                context.asset_partition_key_range
            )

            context.log.debug(f"Loading {len(partitions)} partitions...")

            objs: list[Any] = []
            for partition in partitions:
                path_with_partition = base_dir / f"{partition}{self.extension}"
                context.log.debug(
                    f"Loading partition from {path_with_partition} using {self.__class__.__name__}"
                )
                try:
                    obj = self.deserialize(path_with_partition, context)
                    objs.append(obj)
                except FileNotFoundError as e:
                    if not allow_missing_partitions:
                        raise e
                    context.log.debug(
                        f"Couldn't load partition {path_with_partition} and skipped it"
                    )
            return objs
        elif issubclass(context.dagster_type.typing_type.__args__[0], expected_type):
            context.log.debug(f"Loading from {path} using {self.__class__.__name__}")
            obj = self.deserialize(path, context)
            context.add_input_metadata(
                {
                    "path": MetadataValue.path(path),
                }
            )
            return obj
        else:
            return check.failed(
                f"Inputs of type {context.dagster_type} not supported. Please specify "
                "for this input either in the op signature, corresponding In or in the IOManager annotations."
            )

    def handle_output(self, context: OutputContext, obj: Any):
        path = self.get_path(context)
        path.parent.mkdir(parents=True, exist_ok=True)
        context.log.debug(f"Saving to {path} using {self.__class__.__name__}")
        self.serialize(obj, path, context)

        context.add_output_metadata(
            {"path": MetadataValue.path(path), **self.get_metadata(obj, context)}
        )
