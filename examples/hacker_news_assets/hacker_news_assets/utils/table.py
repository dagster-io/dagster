import textwrap
from typing import Any, Callable, Mapping, NamedTuple, Optional, Set

from dagster import OpDefinition
from dagster.core.asset_defs.asset_in import AssetIn
from dagster.core.asset_defs.decorators import _Asset


class Column(NamedTuple):
    type_name: str
    description: str


def table(
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    ins: Optional[Mapping[str, AssetIn]] = None,
    metadata: Optional[Mapping[str, Any]] = None,
    description: Optional[str] = None,
    required_resource_keys: Optional[Set[str]] = None,
    io_manager_key: Optional[str] = None,
    columns: Optional[Mapping[str, Column]] = None,
) -> Callable[[Callable[..., Any]], OpDefinition]:
    """Create an op that computes a table asset.
    Each argument to the decorated function references an upstream asset that this table depends on.
    The name of the argument designates the name of the upstream asset.
    Args:
        name (Optional[str]): The name of the table.  If not provided, defaults to the name of the
            decorated function.
        namespace (Optional[str]): The namespace that the table resides in.  The namespace + the
            name forms the asset key.
        ins (Optional[Mapping[str, AssetIn]]): A dictionary that maps input names to their metadata
            and namespaces.
        metadata (Optional[Dict[str, Any]]): A dict of metadata entries for the asset.
        required_resource_keys (Optional[Set[str]]): Set of resource handles required by the op.
        io_manager_key (Optional[str]): The resource key of the IOManager used for storing the
            output of the op as an asset, and for loading it in downstream ops
            (default: "io_manager").
    """
    if callable(name):
        return _Asset()(name)

    def inner(fn: Callable[..., Any]) -> OpDefinition:
        final_description = textwrap.dedent(description or fn.__doc__ or "") + columns_to_markdown(
            columns
        )
        return _Asset(
            name=name,
            namespace=namespace,
            ins=ins,
            metadata=metadata,
            description=final_description,
            required_resource_keys=required_resource_keys,
            io_manager_key=io_manager_key,
        )(fn)

    return inner


def columns_to_markdown(columns: Optional[Mapping[str, Column]]) -> str:
    if not columns:
        return ""

    return (
        textwrap.dedent(
            """
        | Name | Type | Description |
        | - | - | - |
    """
        )
        + "\n".join(
            [
                f"| {name} | {column.type_name} | {column.description} |"
                for name, column in columns.items()
            ]
        )
    )
