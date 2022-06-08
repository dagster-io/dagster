import operator
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, NamedTuple, Optional, Sequence, Union, cast

import dagster._check as check
from dagster.core.definitions.asset_layer import build_asset_selection_job
from dagster.core.selector.subset_selector import parse_clause

if TYPE_CHECKING:
    from dagster.core.asset_defs import AssetsDefinition, SourceAsset
    from dagster.core.asset_defs.asset_selection import AssetSelection
    from dagster.core.definitions import ExecutorDefinition, JobDefinition


class UnresolvedAssetJobDefinition(
    NamedTuple(
        "_UnresolvedAssetJobDefinition",
        [
            ("name", str),
            ("selection", "AssetSelection"),
            ("executor_def", Optional["ExecutorDefinition"]),
            ("description", Optional[str]),
            ("tags", Optional[Dict[str, Any]]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        selection: "AssetSelection",
        executor_def: Optional["ExecutorDefinition"] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        from dagster.core.asset_defs.asset_selection import AssetSelection
        from dagster.core.definitions.executor_definition import ExecutorDefinition

        return super(UnresolvedAssetJobDefinition, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            selection=check.inst_param(selection, "selection", AssetSelection),
            executor_def=check.opt_inst_param(executor_def, "executor_def", ExecutorDefinition),
            description=check.opt_str_param(description, "description"),
            tags=check.opt_dict_param(tags, "tags"),
        )

    def resolve(
        self, assets: Sequence["AssetsDefinition"], source_assets: Sequence["SourceAsset"]
    ) -> "JobDefinition":
        """
        Resolve this UnresolvedAssetJobDefinition into a JobDefinition.
        """
        return build_asset_selection_job(
            name=self.name,
            assets=assets,
            source_assets=source_assets,
            executor_def=self.executor_def,
            description=self.description,
            tags=self.tags,
            asset_selection=self.selection.resolve(assets),
        )


def _selection_from_string(string: str) -> "AssetSelection":
    from dagster.core.asset_defs.asset_selection import AssetSelection

    if string == "*":
        return AssetSelection.all()

    parts = parse_clause(string)
    if not parts:
        check.failed(f"Invalid selection string: {string}")
    u, item, d = parts

    selection: AssetSelection = AssetSelection.keys(item)
    if u:
        selection = selection.upstream(u)
    if d:
        selection = selection.downstream(d)
    return selection


def define_asset_job(
    name: str,
    selection: Union[str, Sequence[str], "AssetSelection"] = None,
    executor_def: "ExecutorDefinition" = None,
    description: str = None,
    tags: Dict[str, Any] = None,
) -> UnresolvedAssetJobDefinition:
    """Creates a definition of a job which will update a selection of assets. This will only be
    resolved to a JobDefinition once placed in a repository.
    """
    from dagster.core.asset_defs.asset_selection import AssetSelection

    selection = check.opt_inst_param(
        selection, "selection", (str, list, AssetSelection), default=AssetSelection.all()
    )
    # convert string-based selections to AssetSelection objects
    if isinstance(selection, str):
        selection = _selection_from_string(selection)
    elif isinstance(selection, list):
        check.list_param(selection, "selection", of_type=str)
        selection = reduce(operator.or_, [_selection_from_string(s) for s in selection])

    return UnresolvedAssetJobDefinition(
        name=name,
        selection=cast(AssetSelection, selection),
        executor_def=executor_def,
        description=description,
        tags=tags,
    )
