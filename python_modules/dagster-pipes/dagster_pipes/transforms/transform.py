from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar("T")
U = TypeVar("U")


class TransformContext:
    """Base context for transforms."""

    pass


class TestResult:
    """Result of a data quality test."""

    def __init__(self, passed: bool):
        self.passed = passed


@dataclass
class Upstream:
    asset: str


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
        # Mark function as a transform
        setattr(fn, "__dagster_transforms__", True)

        # Store metadata on the function
        setattr(
            fn,
            "_transform_metadata",
            TransformMetadata(assets=assets or [], checks=checks or []),
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
    if not getattr(fn, "__dagster_transforms__", False):
        raise ValueError(f"Function {fn.__name__} is not a transform")
    return getattr(fn, "_transform_metadata")


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
    if param_name not in fn.__annotations__:
        raise ValueError(f"Parameter {param_name} not found in function {fn.__name__}")

    metadata = fn.__annotations__[param_name].__metadata__
    if not metadata or not isinstance(metadata[0], Upstream):
        raise ValueError(f"Parameter {param_name} does not have Upstream metadata")

    return metadata[0]
