from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Callable, Optional, TypeVar, Union

T = TypeVar("T")
U = TypeVar("U")


class TransformContext:
    """Base context for transforms."""

    pass


class TestResult:
    """Result of a data quality test."""

    def __init__(self, passed: bool):
        self.passed = passed


class Upstream:
    def __init__(self, asset: Union[str, Callable[..., Any]]):
        if callable(asset):
            # Ensure it's a transform
            if not hasattr(asset, TRANSFORM_METADATA_ATTR):
                raise ValueError(f"Callable {asset.__name__} must be decorated with @transform")
            # Get the asset name from the transform metadata
            metadata = getattr(asset, TRANSFORM_METADATA_ATTR)
            if len(metadata.assets) != 1:
                raise ValueError(f"Transform {asset.__name__} must produce exactly one asset")
            self.asset = metadata.assets[0]
        else:
            self.asset = asset

    asset: str


TRANSFORM_METADATA_ATTR = "__dagster_pipes_transform_metadata"


@dataclass
class TransformMetadata:
    """Metadata about a transform including its assets and checks."""

    assets: list[str]
    checks: list[str]


def transform(
    assets: Optional[list[str]] = None,
    checks: Optional[list[str]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for defining transforms that produce assets and/or checks.

    Args:
        assets: list of asset names
        checks: list of check names
    """

    def decorator(fn: Callable[..., T]) -> Callable[..., T]:
        # Store metadata on the function
        setattr(
            fn,
            TRANSFORM_METADATA_ATTR,
            TransformMetadata(assets=assets or [], checks=checks or []),
        )

        # Validate that all non-context parameters have Upstream annotations
        import inspect

        sig = inspect.signature(fn)
        for param_name in sig.parameters.keys():
            if param_name != "context" and param_name in fn.__annotations__:
                metadata = fn.__annotations__[param_name].__metadata__
                if not metadata or not isinstance(metadata[0], Upstream):
                    raise ValueError(
                        f"Parameter {param_name} must be annotated with Upstream metadata"
                    )

        return fn

    return decorator


def get_transform_metadata(fn: Callable) -> TransformMetadata:
    """Get the transform metadata from a function.

    Args:
        fn: The function to get metadata from

    Returns:
        The transform metadata

    Raises:
        ValueError: If the function is not a transform
    """
    if not getattr(fn, TRANSFORM_METADATA_ATTR, False):
        raise ValueError(f"Function {fn.__name__} is not a transform")
    return getattr(fn, TRANSFORM_METADATA_ATTR)


def is_transform_fn(fn: Callable) -> bool:
    """Check if a function is a transform.

    Args:
        fn: The function to check

    Returns:
        True if the function is a transform, False otherwise
    """
    return hasattr(fn, TRANSFORM_METADATA_ATTR)


def get_upstream_metadata(fn: Callable, param_name: str) -> Upstream:
    """Get the Upstream metadata for a parameter in a function.

    Args:
        fn: The function to get metadata from
        param_name: The name of the parameter to get metadata for

    Returns:
        The Upstream metadata for the parameter

    Raises:
        ValueError: If the parameter does not have Upstream metadata
    """
    if param_name == "return":
        raise ValueError("Return value cannot be annotated with Upstream metadata")

    if param_name not in fn.__annotations__:
        raise ValueError(
            f"Parameter '{param_name}' in function '{fn.__name__}' must be annotated with a type. "
            f"Expected format: Annotated[Type, Upstream(asset='asset_name')]"
        )

    annotation = fn.__annotations__[param_name]
    if not hasattr(annotation, "__metadata__"):
        raise ValueError(
            f"Parameter '{param_name}' in function '{fn.__name__}' must be annotated with Annotated[Type, Upstream]. "
            f"Got: {annotation}. Expected format: Annotated[Type, Upstream(asset='asset_name')]"
        )

    metadata = annotation.__metadata__
    if not metadata or not isinstance(metadata[0], Upstream):
        raise ValueError(
            f"Parameter '{param_name}' in function '{fn.__name__}' must be annotated with Upstream metadata. "
            f"Expected format: Annotated[Type, Upstream(asset='asset_name')]"
        )

    return metadata[0]


T = TypeVar("T")


class StorageContext: ...


class TransformResult:
    def __init__(self, assets: dict[str, Any], checks: dict[str, Any]):
        self.assets = assets
        self.checks = checks

    @classmethod
    def asset(cls, asset_key: str, data: Any) -> "TransformResult":
        return cls(assets={asset_key: data}, checks={})

    @classmethod
    def check(cls, check_key: str, data: Any) -> "TransformResult":
        return cls(assets={}, checks={check_key: data})


# Build inputs dictionary by loading upstream data
def build_transform_inputs(
    transform_fn: Callable[..., TransformResult], load_fn: Callable[[str], Any]
) -> dict[str, Any]:
    """Build a dictionary of inputs for a transform function.

    Args:
        transform_fn: The transform function to build inputs for
        load_fn: Function to load data from storage

    Returns:
        Dictionary mapping parameter names to their values
    """
    inputs: dict[str, Any] = {}
    for param_name in transform_fn.__annotations__.keys():
        if param_name == "context":
            continue
        if param_name == "return":
            continue
        upstream = get_upstream_metadata(transform_fn, param_name)
        inputs[param_name] = load_fn(upstream.asset)
    return inputs


def invoke_transform(
    transform_fn: Callable[..., TransformResult], inputs: dict[str, Any]
) -> TransformResult:
    """Invoke a transform function with the given inputs.

    Args:
        transform_fn: The transform function to invoke
        inputs: Dictionary of inputs to pass to the transform function

    Returns:
        The output of the transform function
    """
    return transform_fn(**{**inputs, **{"context": TransformContext()}})


class StorageResult:
    def __init__(self, transform_result: TransformResult):
        self.assets = transform_result.assets
        self.checks = transform_result.checks


class StorageIOPlugin:
    def callable_for_transform(
        self, transform_fn: Callable[..., TransformResult]
    ) -> Callable[[], StorageResult]: ...

    # default implementation of invoke
    def invoke(
        self, *, transform_fn: Callable[..., TransformResult], transform_metadata: TransformMetadata
    ) -> StorageResult:
        inputs = build_transform_inputs(transform_fn, self.load)
        output = invoke_transform(transform_fn, inputs)
        transform_metadata = get_transform_metadata(transform_fn)
        if len(transform_metadata.assets) != 1:
            raise ValueError(
                f"Transform {transform_fn.__name__} must produce exactly one asset. "
                f"Got {len(transform_metadata.assets)} assets: {transform_metadata.assets}"
            )
        if len(transform_metadata.checks) != 0:
            raise ValueError(
                f"Transform {transform_fn.__name__} must not produce any checks. "
                f"Got {len(transform_metadata.checks)} checks: {transform_metadata.checks}"
            )
        self.save(transform_metadata.assets[0], output.assets[transform_metadata.assets[0]])
        return StorageResult(output)

    def load(self, asset_key: str) -> Any: ...
    def save(self, asset_key: str, data: Any) -> None: ...


class InMemoryStorageIO(StorageIOPlugin):
    def __init__(self):
        self.storage: dict[str, Any] = {}

    def load(self, asset_key: str) -> Any:
        return self.storage[asset_key]

    def save(self, asset_key: str, data: Any) -> None:
        self.storage[asset_key] = data


class FileStorageIO(StorageIOPlugin):
    """StorageIO implementation that stores data in temporary files.

    Uses a well-known temp directory that can be accessed by multiple processes.
    Files are stored as pickle files for serialization.
    """

    def __init__(self, temp_dir: Optional[str] = None):
        """Initialize FileStorageIO.

        Args:
            temp_dir: Optional directory to store files in. If not provided,
                     uses system temp directory.
        """
        import os
        import tempfile

        if temp_dir is None:
            temp_dir = tempfile.gettempdir()

        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)

    def _get_filepath(self, asset_key: str) -> str:
        """Get the filepath for an asset key.

        Args:
            asset_key: The asset key to get the filepath for

        Returns:
            The filepath for the asset
        """
        import os

        # Sanitize asset key to be filesystem safe
        safe_key = asset_key.replace("/", "_")
        return os.path.join(self.temp_dir, f"{safe_key}.pkl")

    def load(self, asset_key: str) -> Any:
        """Load data for an asset key from disk.

        Args:
            asset_key: The asset key to load

        Returns:
            The loaded data

        Raises:
            FileNotFoundError: If the asset file doesn't exist
        """
        import pickle

        filepath = self._get_filepath(asset_key)
        with open(filepath, "rb") as f:
            return pickle.load(f)

    def save(self, asset_key: str, data: Any) -> None:
        """Save data for an asset key to disk.

        Args:
            asset_key: The asset key to save
            data: The data to save
        """
        import pickle

        filepath = self._get_filepath(asset_key)
        with open(filepath, "wb") as f:
            pickle.dump(data, f)


def execute_transform(
    transform_fn: Callable[..., TransformResult],
    storage_io: StorageIOPlugin,
) -> StorageResult:
    return BoundTransformGraph(
        transforms=[transform_fn],
        storage_io=storage_io,
    ).execute_transform(transform_fn)


def execute_asset_key(
    asset_key: str,
    storage_io: StorageIOPlugin,
    transforms: list[Callable[..., Any]],
) -> StorageResult:
    return BoundTransformGraph(
        transforms=transforms,
        storage_io=storage_io,
    ).execute_asset_key(asset_key)


@dataclass
class BoundTransformGraph:
    """A mounted transform graph that can execute transforms with storage IO."""

    transforms: list[Callable[..., Any]]
    storage_io: StorageIOPlugin

    def execute_transform(self, transform_fn: Callable[..., Any]) -> StorageResult:
        """Execute a single transform in the graph.

        Args:
            transform_fn: The transform function to execute

        Returns:
            The output of the transform
        """
        return self.storage_io.invoke(
            transform_fn=transform_fn,
            transform_metadata=get_transform_metadata(transform_fn),
        )

    def execute_asset_key(self, asset_key: str) -> StorageResult:
        """Execute the transform that produces the given asset key.

        Args:
            asset_key: The asset key to execute

        Returns:
            The output of the transform

        Raises:
            ValueError: If no transform produces the given asset key
        """
        # Find transform that produces this asset
        for transform_fn in self.transforms:
            metadata = get_transform_metadata(transform_fn)
            if asset_key in metadata.assets:
                return self.execute_transform(transform_fn)

        raise ValueError(f"No transform found that produces asset {asset_key}")


@contextmanager
def mount_transform_graph(
    transforms: list[Callable[..., Any]],
    storage_io: StorageIOPlugin,
) -> Generator[BoundTransformGraph, None, None]:
    """Mount a transform graph with storage IO.

    Args:
        transforms: List of transform functions to execute
        storage_io: Storage IO implementation for loading/saving data

    Yields:
        A TransformGraph instance that can execute transforms
    """
    graph = BoundTransformGraph(
        transforms=transforms,
        storage_io=storage_io,
    )

    yield graph
