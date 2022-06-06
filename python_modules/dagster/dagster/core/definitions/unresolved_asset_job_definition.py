from typing import NamedTuple, Dict, Optional, Any, TYPE_CHECKING, Sequence

from dagster.core.definitions.asset_layer import build_asset_selection_job
import dagster._check as check

if TYPE_CHECKING:
    from dagster.core.asset_defs import AssetsDefinition, SourceAsset
    from dagster.core.definitions import JobDefinition, ExecutorDefinition


class UnresolvedAssetJobDefinition(
    NamedTuple(
        "_UnresolvedAssetJobDefinition",
        [
            ("name", str),
            ("selection", str),
            ("executor_def", Optional["ExecutorDefinition"]),
            ("description", Optional[str]),
            ("tags", Optional[Dict[str, Any]]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        selection: str,
        executor_def: Optional["ExecutorDefinition"] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
    ):
        return super(UnresolvedAssetJobDefinition, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            selection=check.str_param(selection, "selection"),
            executor_def=executor_def,
            description=check.opt_str_param(description, "description"),
            tags=check.opt_dict_param(tags, "tags"),
        )

    def resolve(
        self, assets: Sequence["AssetsDefinition"], source_assets: Sequence["SourceAsset"]
    ) -> "JobDefinition":
        """
        Resolve this UnresolvedAssetJobDefinition into a JobDefinition.
        """
        from dagster.core.selector.subset_selector import parse_asset_selection

        # get a set of selected asset keys
        selected_asset_keys = parse_asset_selection(assets, [self.selection])

        return build_asset_selection_job(
            name=self.name,
            assets=assets,
            source_assets=source_assets,
            executor_def=self.executor_def,
            description=self.description,
            tags=self.tags,
            asset_selection=selected_asset_keys,
            # all assets have resources bound
            resource_defs={},
        )
