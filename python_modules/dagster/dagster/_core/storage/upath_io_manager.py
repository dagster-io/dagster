from abc import abstractmethod
from typing import Any, Dict, Mapping, Optional, Union

from upath import UPath

from dagster import (
    InputContext,
    MetadataValue,
    MultiPartitionKey,
    OutputContext,
    _check as check,
)
from dagster._core.storage.memoizable_io_manager import MemoizableIOManager


class UPathIOManager(MemoizableIOManager):
    """Abstract IOManager base class compatible with local and cloud storage via `universal-pathlib` and `fsspec`.

    Features:
     - handles partitioned assets
     - handles loading a single upstream partition
     - handles loading multiple upstream partitions (with respect to <PyObject object="PartitionMapping" />)
     - the `get_metadata` method can be customized to add additional metadata to the output
     - the `allow_missing_partitions` metadata value can be set to `True` to skip missing partitions
       (the default behavior is to raise an error)

    """

    extension: Optional[str] = None  # override in child class

    def __init__(
        self,
        base_path: Optional[UPath] = None,
    ):
        assert not self.extension or "." in self.extension
        self._base_path = base_path or UPath(".")

    @abstractmethod
    def dump_to_path(self, context: OutputContext, obj: Any, path: UPath):
        """Child classes should override this method to write the object to the filesystem."""

    @abstractmethod
    def load_from_path(self, context: InputContext, path: UPath) -> Any:
        """Child classes should override this method to load the object from the filesystem."""

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

    def unlink(self, path: UPath) -> None:
        """Remove the file or object at the provided path."""
        path.unlink()

    def path_exists(self, path: UPath) -> bool:
        """Check if a file or object exists at the provided path."""
        return path.exists()

    def make_directory(self, path: UPath):
        """Create a directory at the provided path.

        Override as a no-op if the target backend doesn't use directories.
        """
        path.mkdir(parents=True, exist_ok=True)

    def has_output(self, context: OutputContext) -> bool:
        return self.path_exists(self._get_path(context))

    def _with_extension(self, path: UPath) -> UPath:
        return UPath(f"{path}{self.extension}") if self.extension else path

    def _get_path_without_extension(self, context: Union[InputContext, OutputContext]) -> UPath:
        if context.has_asset_key:
            context_path = self.get_asset_relative_path(context)
        else:
            # we are dealing with an op output
            context_path = self.get_op_output_relative_path(context)

        return self._base_path.joinpath(context_path)

    def get_asset_relative_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        # we are not using context.get_asset_identifier() because it already includes the partition_key
        return UPath(*context.asset_key.path)

    def get_op_output_relative_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        return UPath(*context.get_identifier())

    def get_loading_input_log_message(self, path: UPath) -> str:
        return f"Loading file from: {path}"

    def get_writing_output_log_message(self, path: UPath) -> str:
        return f"Writing file at: {path}"

    def _get_path(self, context: Union[InputContext, OutputContext]) -> UPath:
        """Returns the I/O path for a given context.
        Should not be used with partitions (use `_get_paths_for_partitions` instead).
        """
        path = self._get_path_without_extension(context)
        return self._with_extension(path)

    def _get_paths_for_partitions(
        self, context: Union[InputContext, OutputContext]
    ) -> Dict[str, UPath]:
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

        formatted_partition_keys = [
            _formatted_multipartitioned_path(pk) if isinstance(pk, MultiPartitionKey) else pk
            for pk in context.asset_partition_keys
        ]

        asset_path = self._get_path_without_extension(context)
        return {
            partition_key: self._with_extension(asset_path / partition_key)
            for partition_key in formatted_partition_keys
        }

    def _get_multipartition_backcompat_paths(
        self, context: Union[InputContext, OutputContext]
    ) -> Mapping[str, UPath]:
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
        self, path: UPath, context: InputContext, backcompat_path: Optional[UPath] = None
    ) -> Any:
        context.log.debug(self.get_loading_input_log_message(path))
        try:
            obj = self.load_from_path(context=context, path=path)
        except FileNotFoundError as e:
            if backcompat_path is not None:
                try:
                    obj = self.load_from_path(context=context, path=backcompat_path)
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

    def _load_multiple_inputs(self, context: InputContext) -> Dict[str, Any]:
        # load multiple partitions
        allow_missing_partitions = (
            context.metadata.get("allow_missing_partitions", False)
            if context.metadata is not None
            else False
        )

        objs: Dict[str, Any] = {}
        paths = self._get_paths_for_partitions(context)
        backcompat_paths = self._get_multipartition_backcompat_paths(context)

        context.log.debug(f"Loading {len(paths)} partitions...")

        for partition_key, path in paths.items():
            context.log.debug(f"Loading partition from {path} using {self.__class__.__name__}")
            try:
                obj = self.load_from_path(context=context, path=path)
                objs[partition_key] = obj
            except FileNotFoundError as e:
                backcompat_path = backcompat_paths.get(partition_key)
                if backcompat_path is not None:
                    obj = self.load_from_path(context=context, path=backcompat_path)
                    objs[partition_key] = obj

                if not allow_missing_partitions and objs.get(partition_key) is None:
                    raise e

                context.log.debug(
                    f"Couldn't load partition {path} and skipped it "
                    "because the input metadata includes allow_missing_partitions=True"
                )

        # TODO: context.add_output_metadata fails in the partitioned context. this should be fixed?
        return objs

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
