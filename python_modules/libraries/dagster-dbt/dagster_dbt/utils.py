from argparse import Namespace
from collections.abc import Mapping
from typing import TYPE_CHECKING, AbstractSet, Any, Optional, cast  # noqa: UP035

import dagster_shared.check as check
import orjson
from dagster import AssetKey
from dagster._utils.names import clean_name_lower
from packaging import version

from dagster_dbt.compat import DBT_PYTHON_VERSION

if TYPE_CHECKING:
    from dagster_dbt.core.resource import DbtProject

# dbt resource types that may be considered assets
ASSET_RESOURCE_TYPES = ["model", "seed", "snapshot"]


clean_name = clean_name_lower


def default_node_info_to_asset_key(node_info: Mapping[str, Any]) -> AssetKey:
    return AssetKey(node_info["unique_id"].split("."))


def dagster_name_fn(dbt_resource_props: Mapping[str, Any]) -> str:
    return dbt_resource_props["unique_id"].replace(".", "_").replace("-", "_").replace("*", "_star")


def select_unique_ids(
    select: str,
    exclude: str,
    selector: str,
    project: Optional["DbtProject"],
    manifest_json: Mapping[str, Any],
) -> AbstractSet[str]:
    """Given dbt selection paramters, return the unique ids of all resources that match that selection."""
    manifest_version = version.parse(manifest_json.get("metadata", {}).get("dbt_version", "0.0.0"))
    # using dbt Fusion, efficient to invoke the CLI for selection
    if manifest_version.major >= 2 and project is not None:
        return _select_unique_ids_from_cli(select, exclude, selector, project)
    # using dbt-core, too slow to invoke the CLI, so we use library functions instead
    elif DBT_PYTHON_VERSION is not None:
        return _select_unique_ids_from_manifest(select, exclude, selector, manifest_json)
    else:
        # in theory, as long as dbt-core is a dependency of dagster-dbt, this can't happen, but adding
        # this for now to be safe
        check.failed(
            "dbt-core is not installed and no `project` was passed to `select_unique_ids`. "
            "This can happen if you are using the dbt Cloud integration without the dbt-core package installed."
        )


def _select_unique_ids_from_cli(
    select: str,
    exclude: str,
    selector: str,
    project: "DbtProject",
) -> AbstractSet[str]:
    """Uses the available dbt CLI to list the unique ids of the selected models. This is not recommended if
    dbt-core is available, as it will be slower than using the manifest.
    """
    from dagster_dbt.core.resource import DbtCliResource

    cmd = ["list", "--output", "json"]
    if select and select != "fqn:*":
        cmd.append("--select")
        cmd.append(select)
    if exclude:
        cmd.append("--exclude")
        cmd.append(exclude)
    if selector:
        cmd.append("--selector")
        cmd.append(selector)

    raw_events = DbtCliResource(project_dir=project).cli(cmd)._stream_stdout()  # noqa
    unique_ids = set()
    for event in raw_events:
        if isinstance(event, dict):
            try:
                msg = orjson.loads(event.get("info", {}).get("msg", "{}"))
            except orjson.JSONDecodeError:
                continue
            unique_ids.add(msg.get("unique_id"))

    return unique_ids - {None}


def _select_unique_ids_from_manifest(
    select: str, exclude: str, selector: str, manifest_json: Mapping[str, Any]
) -> AbstractSet[str]:
    """Method to apply a selection string to an existing manifest.json file."""
    import dbt.graph.cli as graph_cli
    import dbt.graph.selector as graph_selector
    from dbt.contracts.graph.manifest import Manifest
    from dbt.contracts.graph.nodes import SavedQuery, SemanticModel
    from dbt.contracts.selection import SelectorFile
    from dbt.graph.selector_spec import IndirectSelection, SelectionSpec
    from networkx import DiGraph

    select_specified = select and select != "fqn:*"
    check.param_invariant(
        not ((select_specified or exclude) and selector),
        "selector",
        "Cannot provide both a selector and a select/exclude param.",
    )

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
    if DBT_PYTHON_VERSION is not None and DBT_PYTHON_VERSION >= version.parse("1.8.0"):
        from dbt.contracts.graph.nodes import UnitTestDefinition

        unit_tests = (
            {
                "unit_tests": {
                    # Starting in dbt 1.8 unit test nodes must be defined using the UnitTestDefinition class
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
                    # Semantic model nodes must be defined using the SemanticModel class
                    unique_id: SemanticModel.from_dict(info)
                    for unique_id, info in manifest_json["semantic_models"].items()
                },
            }
            if manifest_json.get("semantic_models")
            else {}
        ),
        **(
            {
                "saved_queries": {
                    # Saved query nodes must be defined using the SavedQuery class
                    unique_id: SavedQuery.from_dict(info)
                    for unique_id, info in manifest_json["saved_queries"].items()
                },
            }
            if manifest_json.get("saved_queries")
            else {}
        ),
        **(
            {
                "selectors": {
                    unique_id: _DictShim(info)
                    for unique_id, info in manifest_json["selectors"].items()
                }
            }
            if manifest_json.get("selectors")
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

    if selector:
        # must parse all selectors to handle dependencies, then grab the specific selector
        # that was specified
        result = graph_cli.parse_from_selectors_definition(
            source=SelectorFile.from_dict({"selectors": manifest.selectors.values()})
        )
        if selector not in result:
            raise ValueError(f"Selector `{selector}` not found in manifest.")
        parsed_spec: SelectionSpec = cast("SelectionSpec", result[selector]["definition"])
    else:
        parsed_spec: SelectionSpec = graph_cli.parse_union([select], True)

    if exclude:
        parsed_exclude_spec = graph_cli.parse_union([exclude], False)
        parsed_spec = graph_cli.SelectionDifference(components=[parsed_spec, parsed_exclude_spec])

    # execute this selection against the graph
    node_selector = graph_selector.NodeSelector(graph, manifest)
    selected, _ = node_selector.select_nodes(parsed_spec)
    return selected


def _set_flag_attrs(kvs: dict[str, Any]):
    from dbt.flags import get_flag_dict, set_flags

    new_flags = Namespace()
    for global_key, global_value in get_flag_dict().items():
        setattr(new_flags, global_key.upper(), global_value)
    for key, value in kvs.items():
        setattr(new_flags, key.upper(), value)
    set_flags(new_flags)
