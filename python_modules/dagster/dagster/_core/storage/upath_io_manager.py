from __future__ import annotations

import inspect
from abc import abstractmethod
from typing import Any, Dict, Union

from upath import UPath

from dagster import (
    InputContext,
    MetadataValue,
    OutputContext,
    _check as check,
)
from dagster._core.storage.memoizable_io_manager import MemoizableIOManager


class UPathIOManager(MemoizableIOManager):
    """
    Abstract IOManager base class compatible with local and cloud storage via `universal-pathlib` and `fsspec`.

    Features:
     - handles partitioned assets
     - handles loading a single upstream partition
     - handles loading multiple upstream partitions (with respect to <PyObject object="PartitionMapping" />)
     - the `get_metadata` method can be customized to add additional metadata to the output
     - the `allow_missing_partitions` metadata value can be set to `True` to skip missing partitions
       (the default behavior is to raise an error)

    """

    extension: str = ""  # override in child class

    def __init__(
        self,
        base_path: UPath,
    ):
        assert self.extension == "" or "." in self.extension

        self._base_path = base_path

    @abstractmethod
    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
        """Child classes should override this method to write the object to the filesystem."""

    @abstractmethod
    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        """Child classes should override this method to load the object from the filesystem."""

    def get_metadata(
        self,
        context: OutputContext,  # pylint: disable=unused-argument
        obj: Any,  # pylint: disable=unused-argument
    ) -> Dict[str, MetadataValue]:
        """Child classes should override this method to add custom metadata to the outputs."""
        return {}

    def has_output(self, context: OutputContext) -> bool:
        return self._get_path(context).exists()

    def _get_path_without_extension(self, context: Union[InputContext, OutputContext]) -> UPath:
        if context.has_asset_key:
            # we are dealing with an asset

            # we are not using context.get_asset_identifier() because it already includes the partition_key
            context_path = list(context.asset_key.path)
        else:
            # we are dealing with an op output
            context_path = list(context.get_identifier())

        return self._base_path.joinpath(*context_path)

    def _get_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        """
        Returns the I/O path for a given context.
        Should not be used with partitions (use `_get_paths_for_partitions` instead).
        """
        return self._get_path_without_extension(context).with_suffix(self.extension)

    def _get_paths_for_partitions(
        self, context: Union[InputContext, OutputContext]
    ) -> Dict[str, UPath]:
        """
        Returns a dict of partition_keys into I/O paths for a given context.
        """
        if not context.has_asset_partitions:
            raise TypeError(
                f"Detected {context.dagster_type.typing_type} input type "
                "but the asset is not partitioned"
            )

        partition_keys = context.asset_partition_keys
        asset_path = self._get_path_without_extension(context)
        return {
            partition_key: (asset_path / partition_key).with_suffix(self.extension)
            for partition_key in partition_keys
        }

    def _load_single_input(self, path: UPath, context: InputContext) -> Any:
        context.log.debug(f"Loading file from: {path}")
        obj = self.load_from_path(context=context, path=path)
        context.add_input_metadata({"path": MetadataValue.path(str(path))})
        return obj

    def _load_multiple_inputs(self, context: InputContext) -> Dict[str, Any]:
        # load multiple partitions
        allow_missing_partitions = (
            context.metadata.get("allow_missing_partitions", False)
            if context.metadata is not None
            else False
        )

        objs: Dict[str, Any] = {}
        paths = self._get_paths_for_partitions(context)

        context.log.debug(f"Loading {len(paths)} partitions...")

        for partition_key, path in paths.items():
            context.log.debug(f"Loading partition from {path} using {self.__class__.__name__}")
            try:
                obj = self.load_from_path(context=context, path=path)
                objs[partition_key] = obj
            except FileNotFoundError as e:
                if not allow_missing_partitions:
                    raise e
                context.log.debug(
                    f"Couldn't load partition {path} and skipped it "
                    "because the input metadata includes allow_missing_partitions=True"
                )

        # TODO: context.add_output_metadata fails in the partitioned context. this should be fixed?
        return objs

    def load_input(self, context: InputContext) -> Union[Any, Dict[str, Any]]:
        if not context.has_asset_key:
            # we are dealing with an op output which is always non-partitioned
            path = self._get_path(context)
            return self._load_single_input(path, context)
        else:
            if not context.has_asset_partitions:
                # we are dealing with a non-partitioned asset
                path = self._get_path(context)
                return self._load_single_input(path, context)
            else:
                expected_type = inspect.signature(self.load_from_path).return_annotation

                asset_partition_keys = context.asset_partition_keys
                if len(asset_partition_keys) == 0:
                    return None
                elif len(asset_partition_keys) == 1:
                    if (
                        hasattr(context.dagster_type.typing_type, "__origin__")
                        and context.dagster_type.typing_type.__origin__ in (Dict, dict)
                        and context.dagster_type.typing_type.__args__[1] == expected_type
                    ):
                        # the asset type annotation is accidentally a Dict[str, expected_type]
                        # even tho no partition mappings are used
                        return check.failed(
                            f"Received `{context.dagster_type.typing_type}` type in input of"
                            f" DagsterType {context.dagster_type}, but `{self.load_from_path}` has"
                            f" {expected_type} type annotation for obj. They should match. If you"
                            " are loading a single partition, the upstream asset type annotation"
                            " should not be a typing.Dict, but a single partition type."
                        )

                    # we are dealing with a single partition of a non-partitioned asset
                    paths = self._get_paths_for_partitions(context)
                    check.invariant(len(paths) == 1, f"Expected 1 path, but got {len(paths)}")
                    path = list(paths.values())[0]
                    return self._load_single_input(path, context)
                else:
                    # we are dealing with multiple partitions of an asset

                    if (
                        context.dagster_type.typing_type != Any
                    ):  # skip type checking if the type is Any
                        if context.dagster_type.typing_type == expected_type:
                            # error message if the user forgot to specify a Dict type
                            # this case is checked separately because this type of mistake can be very common
                            return check.failed(
                                f"Received `{context.dagster_type.typing_type}` type in input"
                                f" DagsterType {context.dagster_type}, but the input has multiple"
                                f" partitions. `Dict[str, {context.dagster_type.typing_type}]`"
                                " should be used in this case."
                            )

                        elif (
                            hasattr(context.dagster_type.typing_type, "__origin__")
                            and context.dagster_type.typing_type.__origin__ in (Dict, dict)
                            and context.dagster_type.typing_type.__args__[1] == expected_type
                        ):
                            # type checking passed
                            return self._load_multiple_inputs(context)
                        else:
                            # something is wrong with the types
                            return check.failed(
                                f"Received `{context.dagster_type.typing_type}` type in input of"
                                f" DagsterType {context.dagster_type}, but `{self.load_from_path}`"
                                f" has {expected_type} type annotation for obj. They should be both"
                                " specified with type annotations and match. If you are loading"
                                " multiple partitions, the upstream asset type annotation should"
                                " be a typing.Dict."
                            )
                    else:
                        return self._load_multiple_inputs(context)

    def handle_output(self, context: OutputContext, obj: Any):
        if context.dagster_type.typing_type == type(None):
            check.invariant(
                obj is None,
                (
                    "Output had Nothing type or 'None' annotation, but handle_output received"
                    f" value that was not None and was of type {type(obj)}."
                ),
            )
            return None

        if context.has_asset_partitions:
            paths = self._get_paths_for_partitions(context)
            assert len(paths) == 1
            path = list(paths.values())[0]
        else:
            path = self._get_path(context)
        path.parent.mkdir(parents=True, exist_ok=True)
        context.log.debug(f"Writing file at: {path}")
        self.dump_to_path(context=context, obj=obj, path=path)

        metadata = {"path": MetadataValue.path(str(path))}
        custom_metadata = self.get_metadata(context=context, obj=obj)
        metadata.update(custom_metadata)  # type: ignore

        context.add_output_metadata(metadata)
