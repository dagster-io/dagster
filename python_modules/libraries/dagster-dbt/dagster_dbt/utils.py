from argparse import Namespace
from collections.abc import Mapping
from typing import AbstractSet, Any  # noqa: UP035

from dagster import AssetKey
from packaging import version

# dbt resource types that may be considered assets
ASSET_RESOURCE_TYPES = ["model", "seed", "snapshot"]


def default_node_info_to_asset_key(node_info: Mapping[str, Any]) -> AssetKey:
    return AssetKey(node_info["unique_id"].split("."))


def dagster_name_fn(dbt_resource_props: Mapping[str, Any]) -> str:
    return dbt_resource_props["unique_id"].replace(".", "_").replace("-", "_").replace("*", "_star")


def select_unique_ids_from_manifest(
    select: str,
    exclude: str,
    manifest_json: Mapping[str, Any],
) -> AbstractSet[str]:
    """Method to apply a selection string to an existing manifest.json file."""
    import dbt.graph.cli as graph_cli
    import dbt.graph.selector as graph_selector
    from dbt.contracts.graph.manifest import Manifest
    from dbt.graph.selector_spec import IndirectSelection, SelectionSpec
    from dbt.version import __version__ as dbt_version
    from networkx import DiGraph

    # NOTE: this was faster than calling `Manifest.from_dict`, so we are keeping this.
    class _DictShim(dict):
        """Shim to enable hydrating a dictionary into a dot-accessible object. We need this because
        dbt expects dataclasses that can be accessed with dot notation, not bare dictionaries.

        See https://stackoverflow.com/a/23689767.
        """

        def __getattr__(self, item):
            ret = super().get(item)
            # allow recursive access e.g. foo.bar.baz
            return _DictShim(ret) if isinstance(ret, dict) else ret

    unit_tests = {}
    if version.parse(dbt_version) >= version.parse("1.8.0"):
        from dbt.contracts.graph.nodes import UnitTestDefinition

        unit_tests = (
            {
                "unit_tests": {
                    # unit test nodes must be of type UnitTestDefinition
                    unique_id: UnitTestDefinition.from_dict(info)
                    for unique_id, info in manifest_json["unit_tests"].items()
                },
            }
            if manifest_json.get("unit_tests")
            else {}
        )

    manifest = Manifest(
        nodes={unique_id: _DictShim(info) for unique_id, info in manifest_json["nodes"].items()},
        sources={
            unique_id: _DictShim(info)
            for unique_id, info in manifest_json["sources"].items()  # type: ignore
        },
        metrics={
            unique_id: _DictShim(info)
            for unique_id, info in manifest_json["metrics"].items()  # type: ignore
        },
        exposures={
            unique_id: _DictShim(info)
            for unique_id, info in manifest_json["exposures"].items()  # type: ignore
        },
        **(  # type: ignore
            {
                "semantic_models": {
                    unique_id: _DictShim(info)
                    for unique_id, info in manifest_json["semantic_models"].items()
                }
            }
            if manifest_json.get("semantic_models")
            else {}
        ),
        **(
            {
                "saved_queries": {
                    unique_id: _DictShim(info)
                    for unique_id, info in manifest_json["saved_queries"].items()
                },
            }
            if manifest_json.get("saved_queries")
            else {}
        ),
        **unit_tests,
    )
    child_map = manifest_json["child_map"]

    graph = graph_selector.Graph(DiGraph(incoming_graph_data=child_map))

    # create a parsed selection from the select string
    _set_flag_attrs(
        {
            "INDIRECT_SELECTION": IndirectSelection.Eager,
            "WARN_ERROR": True,
        }
    )
    parsed_spec: SelectionSpec = graph_cli.parse_union([select], True)

    if exclude:
        parsed_exclude_spec = graph_cli.parse_union([exclude], False)
        parsed_spec = graph_cli.SelectionDifference(components=[parsed_spec, parsed_exclude_spec])

    # execute this selection against the graph
    selector = graph_selector.NodeSelector(graph, manifest)
    selected, _ = selector.select_nodes(parsed_spec)
    return selected


def get_dbt_resource_props_by_dbt_unique_id_from_manifest(
    manifest: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    """A mapping of a dbt node's unique id to the node's dictionary representation in the manifest."""
    return {
        **manifest["nodes"],
        **manifest["sources"],
        **manifest["exposures"],
        **manifest["metrics"],
        **manifest.get("semantic_models", {}),
        **manifest.get("saved_queries", {}),
        **manifest.get("unit_tests", {}),
    }


def _set_flag_attrs(kvs: dict[str, Any]):
    from dbt.flags import get_flag_dict, set_flags

    new_flags = Namespace()
    for global_key, global_value in get_flag_dict().items():
        setattr(new_flags, global_key.upper(), global_value)
    for key, value in kvs.items():
        setattr(new_flags, key.upper(), value)
    set_flags(new_flags)
