from __future__ import annotations

import inspect
from abc import abstractmethod
from typing import Any, Dict, Mapping, Union

from upath import UPath

from dagster import InputContext, MemoizableIOManager, MetadataValue, OutputContext
from dagster import _check as check
from dagster._annotations import experimental


@experimental
class UPathIOManager(MemoizableIOManager):
    """
    Abstract IOManager base class compatible with local and cloud storage via `fsspec` (using `universal-pathlib`).

    Features:
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

    @abstractmethod
    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        """
        Child classes should override this method to load the object from the filesystem.

        Args:
            context:
            path:

        Returns:

        """

    def get_metadata(
        self, context: OutputContext, obj: Any  # pylint: disable=unused-argument
    ) -> Dict[str, MetadataValue]:
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

    @staticmethod
    def _has_multiple_partitions(context: Union[InputContext, OutputContext]) -> bool:
        assert context.has_asset_partitions, "this should only be used with partitioned assets"
        key_range = context.asset_partition_key_range
        return key_range.start != key_range.end

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
        Args:
            context:

        Returns:

        """
        return self._get_path_without_extension(context).with_suffix(self.extension)

    def _get_paths_for_partitions(
        self, context: Union[InputContext, OutputContext]
    ) -> Mapping[str, UPath]:
        """
        Returns a mapping of partition_keys into I/O paths for a given context.
        Args:
            context:

        Returns:

        """
        if not context.has_asset_partitions:
            raise TypeError(
                f"Detected {context.dagster_type.typing_type} input type "
                f"but the asset is not partitioned"
            )

        partition_keys = context.asset_partition_keys
        asset_path = self._get_path_without_extension(context)

        paths = {}
        for partition_key in partition_keys:
            paths[partition_key] = (asset_path / partition_key).with_suffix(self.extension)

        return paths

    def load_input(self, context: InputContext) -> Union[Any, Dict[str, Any]]:
        if not context.has_asset_partitions or not self._has_multiple_partitions(context):
            # we are not dealing with multiple partitions
            if context.has_asset_partitions:
                # we are dealing with a single partition
                paths = self._get_paths_for_partitions(context)
                assert len(paths) == 1
                path = list(paths.values())[0]
            else:
                # we are dealing with a non-partitioned asset / OP output
                path = self._get_path(context)

            context.log.debug(f"Loading from {path} using {self.__class__.__name__}")
            obj = self.load_from_path(context=context, path=path)

            metadata = {"path": MetadataValue.path(path)}
            custom_metadata = self.get_metadata(obj, context)
            metadata.update(custom_metadata)  # type: ignore
            context.add_input_metadata(metadata)

            return obj
        else:
            # we are dealing with multiple partitions
            # force the user to specify the correct type annotation
            expected_type = inspect.signature(self.dump_to_path).parameters["obj"].annotation

            if context.dagster_type.typing_type == expected_type and self._has_multiple_partitions(
                context
            ):
                return check.failed(
                    f"Received `{context.dagster_type.typing_type.__name__}` type "
                    f"in input DagsterType {context.dagster_type}, "
                    f"but the input has multiple partitions. "
                    f"`Mapping[str, {context.dagster_type.typing_type.__name__}]` should be used in this case."
                )
            elif (
                hasattr(context.dagster_type.typing_type, "__origin__")
                and context.dagster_type.typing_type.__origin__ in (Dict, dict)
                and context.dagster_type.typing_type.__args__[1] == expected_type
                and self._has_multiple_partitions(context)
            ):
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
                    context.log.debug(
                        f"Loading partition from {path} using {self.__class__.__name__}"
                    )
                    try:
                        obj = self.load_from_path(context=context, path=path)
                        objs[partition_key] = obj
                    except FileNotFoundError as e:
                        if not allow_missing_partitions:
                            raise e
                        context.log.debug(
                            f"Couldn't load partition {path} and skipped it "
                            f"because the input metadata includes allow_missing_partitions=True"
                        )

                # TODO: context.add_output_metadata fails in the partitioned context. this should be fixed?
                return objs
            else:
                return check.failed(
                    f"Received `{context.dagster_type.typing_type.__name__}` type "
                    f"in input DagsterType {context.dagster_type}, "
                    f"but `{self.dump_to_path}` has {expected_type} type annotation. "
                    f"They should match."
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
