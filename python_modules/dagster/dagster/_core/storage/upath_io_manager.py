import asyncio
import inspect
from abc import abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Mapping, Optional, Union

from fsspec import AbstractFileSystem
from fsspec.implementations.local import LocalFileSystem

from dagster import (
    InputContext,
    MetadataValue,
    MultiPartitionKey,
    OutputContext,
    _check as check,
)
from dagster._core.storage.memoizable_io_manager import MemoizableIOManager

if TYPE_CHECKING:
    from upath import UPath


class UPathIOManager(MemoizableIOManager):
    """Abstract IOManager base class compatible with local and cloud storage via `universal-pathlib` and `fsspec`.

    Features:
     - handles partitioned assets
     - handles loading a single upstream partition
     - handles loading multiple upstream partitions (with respect to :py:class:`PartitionMapping`)
     - supports loading multiple partitions concurrently with async `load_from_path` method
     - the `get_metadata` method can be customized to add additional metadata to the output
     - the `allow_missing_partitions` metadata value can be set to `True` to skip missing partitions
       (the default behavior is to raise an error)

    """

    extension: Optional[str] = None  # override in child class

    def __init__(
        self,
        base_path: Optional["UPath"] = None,
    ):
        from upath import UPath

        assert not self.extension or "." in self.extension
        self._base_path = base_path or UPath(".")

    @abstractmethod
    def dump_to_path(self, context: OutputContext, obj: Any, path: "UPath"):
        """Child classes should override this method to write the object to the filesystem."""

    @abstractmethod
    def load_from_path(self, context: InputContext, path: "UPath") -> Any:
        """Child classes should override this method to load the object from the filesystem."""

    @property
    def fs(self) -> AbstractFileSystem:
        """Utility function to get the IOManager filesystem.

        Returns:
            AbstractFileSystem: fsspec filesystem.

        """
        from upath import UPath

        if isinstance(self._base_path, UPath):
            return self._base_path.fs
        elif isinstance(self._base_path, Path):
            return LocalFileSystem()
        else:
            raise ValueError(f"Unsupported base_path type: {type(self._base_path)}")

    @property
    def storage_options(self) -> Dict[str, Any]:
        """Utility function to get the fsspec storage_options which are often consumed by various I/O functions.

        Returns:
            Dict[str, Any]: fsspec storage_options.
        """
        from upath import UPath

        if isinstance(self._base_path, UPath):
            return self._base_path._kwargs.copy()  # noqa
        elif isinstance(self._base_path, Path):
            return {}
        else:
            raise ValueError(f"Unsupported base_path type: {type(self._base_path)}")

    def get_metadata(
        self,
        context: OutputContext,
        obj: Any,
    ) -> Dict[str, MetadataValue]:
        """Child classes should override this method to add custom metadata to the outputs."""
        return {}

    # Read/write operations on paths can generally be handled by methods on the
    # UPath class, but when the backend requires credentials, this isn't
    # always possible. Override these path_* methods to provide custom
    # implementations for targeting backends that require authentication.

    def unlink(self, path: "UPath") -> None:
        """Remove the file or object at the provided path."""
        path.unlink()

    def path_exists(self, path: "UPath") -> bool:
        """Check if a file or object exists at the provided path."""
        return path.exists()

    def make_directory(self, path: "UPath"):
        """Create a directory at the provided path.

        Override as a no-op if the target backend doesn't use directories.
        """
        path.mkdir(parents=True, exist_ok=True)

    def has_output(self, context: OutputContext) -> bool:
        return self.path_exists(self._get_path(context))

    def _with_extension(self, path: "UPath") -> "UPath":
        return path.with_suffix(path.suffix + self.extension) if self.extension else path

    def _get_path_without_extension(self, context: Union[InputContext, OutputContext]) -> "UPath":
        if context.has_asset_key:
            context_path = self.get_asset_relative_path(context)
        else:
            # we are dealing with an op output
            context_path = self.get_op_output_relative_path(context)

        return self._base_path.joinpath(context_path)

    def get_asset_relative_path(self, context: Union[InputContext, OutputContext]) -> "UPath":
        from upath import UPath

        # we are not using context.get_asset_identifier() because it already includes the partition_key
        return UPath(*context.asset_key.path)

    def get_op_output_relative_path(self, context: Union[InputContext, OutputContext]) -> "UPath":
        from upath import UPath

        return UPath(*context.get_identifier())

    def get_loading_input_log_message(self, path: "UPath") -> str:
        return f"Loading file from: {path} using {self.__class__.__name__}..."

    def get_writing_output_log_message(self, path: "UPath") -> str:
        return f"Writing file at: {path} using {self.__class__.__name__}..."

    def get_loading_input_partition_log_message(self, path: "UPath", partition_key: str) -> str:
        return f"Loading partition {partition_key} from {path} using {self.__class__.__name__}..."

    def get_missing_partition_log_message(self, partition_key: str) -> str:
        return (
            f"Couldn't load partition {partition_key} and skipped it "
            "because the input metadata includes allow_missing_partitions=True"
        )

    def _get_path(self, context: Union[InputContext, OutputContext]) -> "UPath":
        """Returns the I/O path for a given context.
        Should not be used with partitions (use `_get_paths_for_partitions` instead).
        """
        path = self._get_path_without_extension(context)
        return self._with_extension(path)

    def get_path_for_partition(
        self, context: Union[InputContext, OutputContext], path: "UPath", partition: str
    ) -> "UPath":
        """Override this method if you want to use a different partitioning scheme
        (for example, if the saving function handles partitioning instead).
        The extension will be added later.

        Args:
            context (Union[InputContext, OutputContext]): The context for the I/O operation.
            path (UPath): The path to the file or object.
            partition (str): Formatted partition/multipartition key

        Returns:
            UPath: The path to the file with the partition key appended.
        """
        return path / partition

    def _get_paths_for_partitions(
        self, context: Union[InputContext, OutputContext]
    ) -> Dict[str, "UPath"]:
        """Returns a dict of partition_keys into I/O paths for a given context."""
        if not context.has_asset_partitions:
            raise TypeError(
                f"Detected {context.dagster_type.typing_type} input type "
                "but the asset is not partitioned"
            )

        def _formatted_multipartitioned_path(partition_key: MultiPartitionKey) -> str:
            ordered_dimension_keys = [
                key[1]
                for key in sorted(partition_key.keys_by_dimension.items(), key=lambda x: x[0])
            ]
            return "/".join(ordered_dimension_keys)

        formatted_partition_keys = {
            partition_key: _formatted_multipartitioned_path(partition_key)
            if isinstance(partition_key, MultiPartitionKey)
            else partition_key
            for partition_key in context.asset_partition_keys
        }

        asset_path = self._get_path_without_extension(context)
        return {
            partition_key: self._with_extension(
                self.get_path_for_partition(context, asset_path, partition)
            )
            for partition_key, partition in formatted_partition_keys.items()
        }

    def _get_multipartition_backcompat_paths(
        self, context: Union[InputContext, OutputContext]
    ) -> Mapping[str, "UPath"]:
        if not context.has_asset_partitions:
            raise TypeError(
                f"Detected {context.dagster_type.typing_type} input type "
                "but the asset is not partitioned"
            )

        partition_keys = context.asset_partition_keys

        asset_path = self._get_path_without_extension(context)
        return {
            partition_key: self._with_extension(asset_path / partition_key)
            for partition_key in partition_keys
            if isinstance(partition_key, MultiPartitionKey)
        }

    def _load_single_input(
        self, path: "UPath", context: InputContext, backcompat_path: Optional["UPath"] = None
    ) -> Any:
        context.log.debug(self.get_loading_input_log_message(path))
        try:
            obj = self.load_from_path(context=context, path=path)
            if asyncio.iscoroutine(obj):
                obj = asyncio.run(obj)
        except FileNotFoundError as e:
            if backcompat_path is not None:
                try:
                    obj = self.load_from_path(context=context, path=backcompat_path)
                    if asyncio.iscoroutine(obj):
                        obj = asyncio.run(obj)

                    context.log.debug(
                        f"File not found at {path}. Loaded instead from backcompat path:"
                        f" {backcompat_path}"
                    )
                except FileNotFoundError:
                    raise e
            else:
                raise e

        context.add_input_metadata({"path": MetadataValue.path(str(path))})
        return obj

    def _load_partition_from_path(
        self,
        context: InputContext,
        partition_key: str,
        path: "UPath",
        backcompat_path: Optional["UPath"] = None,
    ) -> Any:
        """1. Try to load the partition from the normal path.
        2. If it was not found, try to load it from the backcompat path.
        3. If allow_missing_partitions metadata is True, skip the partition if it was not found in any of the paths.
        Otherwise, raise an error.

        Args:
            context (InputContext): IOManager Input context
            partition_key (str): the partition key corresponding to the partition being loaded
            path (UPath): The path to the partition.
            backcompat_path (Optional[UPath]): The path to the partition in the backcompat location.

        Returns:
            Any: The object loaded from the partition.
        """
        allow_missing_partitions = (
            context.metadata.get("allow_missing_partitions", False)
            if context.metadata is not None
            else False
        )

        try:
            context.log.debug(self.get_loading_input_partition_log_message(path, partition_key))
            obj = self.load_from_path(context=context, path=path)
            return obj
        except FileNotFoundError as e:
            if backcompat_path is not None:
                try:
                    obj = self.load_from_path(context=context, path=path)
                    context.log.debug(
                        f"File not found at {path}. Loaded instead from backcompat path:"
                        f" {backcompat_path}"
                    )
                    return obj
                except FileNotFoundError as e:
                    if allow_missing_partitions:
                        context.log.warning(self.get_missing_partition_log_message(partition_key))
                        return None
                    else:
                        raise e
            if allow_missing_partitions:
                context.log.warning(self.get_missing_partition_log_message(partition_key))
                return None
            else:
                raise e

    def _load_multiple_inputs(self, context: InputContext) -> Dict[str, Any]:
        # load multiple partitions
        paths = self._get_paths_for_partitions(context)  # paths for normal partitions
        backcompat_paths = self._get_multipartition_backcompat_paths(
            context
        )  # paths for multipartitions

        context.log.debug(f"Loading {len(paths)} partitions...")

        objs = {}

        if not inspect.iscoroutinefunction(self.load_from_path):
            for partition_key in context.asset_partition_keys:
                obj = self._load_partition_from_path(
                    context,
                    partition_key,
                    paths[partition_key],
                    backcompat_paths.get(partition_key),
                )
                if obj is not None:  # in case some partitions were skipped
                    objs[partition_key] = obj
            return objs
        else:
            # load_from_path returns a coroutine, so we need to await the results

            async def collect():
                loop = asyncio.get_running_loop()

                tasks = []

                for partition_key in context.asset_partition_keys:
                    tasks.append(
                        loop.create_task(
                            self._load_partition_from_path(
                                context,
                                partition_key,
                                paths[partition_key],
                                backcompat_paths.get(partition_key),
                            )
                        )
                    )

                results = await asyncio.gather(*tasks, return_exceptions=True)

                # need to handle missing partitions here because exceptions don't get propagated from async calls
                allow_missing_partitions = (
                    context.metadata.get("allow_missing_partitions", False)
                    if context.metadata is not None
                    else False
                )

                results_without_errors = []
                found_errors = False
                for partition_key, result in zip(context.asset_partition_keys, results):
                    if isinstance(result, FileNotFoundError):
                        if allow_missing_partitions:
                            context.log.warning(
                                self.get_missing_partition_log_message(partition_key)
                            )
                        else:
                            context.log.error(str(result))
                            found_errors = True
                    elif isinstance(result, Exception):
                        context.log.error(str(result))
                        found_errors = True
                    else:
                        results_without_errors.append(result)

                if found_errors:
                    raise RuntimeError(
                        f"{len(paths) - len(results_without_errors)} partitions could not be loaded"
                    )

                return results_without_errors

            awaited_objects = asyncio.get_event_loop().run_until_complete(collect())

            return {
                partition_key: awaited_object
                for partition_key, awaited_object in zip(
                    context.asset_partition_keys, awaited_objects
                )
                if awaited_object is not None
            }

    def load_input(self, context: InputContext) -> Union[Any, Dict[str, Any]]:
        # If no asset key, we are dealing with an op output which is always non-partitioned
        if not context.has_asset_key or not context.has_asset_partitions:
            path = self._get_path(context)
            return self._load_single_input(path, context)
        else:
            asset_partition_keys = context.asset_partition_keys
            if len(asset_partition_keys) == 0:
                return None
            elif len(asset_partition_keys) == 1:
                paths = self._get_paths_for_partitions(context)
                check.invariant(len(paths) == 1, f"Expected 1 path, but got {len(paths)}")
                path = list(paths.values())[0]
                backcompat_paths = self._get_multipartition_backcompat_paths(context)
                backcompat_path = (
                    None if not backcompat_paths else list(backcompat_paths.values())[0]
                )

                return self._load_single_input(path, context, backcompat_path)
            else:  # we are dealing with multiple partitions of an asset
                type_annotation = context.dagster_type.typing_type
                if type_annotation != Any and not is_dict_type(type_annotation):
                    check.failed(
                        "Loading an input that corresponds to multiple partitions, but the"
                        " type annotation on the op input is not a dict, Dict, Mapping, or"
                        f" Any: is '{type_annotation}'."
                    )

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
        self.make_directory(path.parent)
        context.log.debug(self.get_writing_output_log_message(path))
        self.dump_to_path(context=context, obj=obj, path=path)

        metadata = {"path": MetadataValue.path(str(path))}
        custom_metadata = self.get_metadata(context=context, obj=obj)
        metadata.update(custom_metadata)  # type: ignore

        context.add_output_metadata(metadata)


def is_dict_type(type_obj) -> bool:
    if type_obj == dict:
        return True

    if hasattr(type_obj, "__origin__") and type_obj.__origin__ in (dict, Dict, Mapping):
        return True

    return False
