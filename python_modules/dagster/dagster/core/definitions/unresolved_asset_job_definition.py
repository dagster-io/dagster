import operator
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, NamedTuple, Optional, Sequence, Union, cast

import dagster._check as check
from dagster.core.definitions.asset_layer import build_asset_selection_job
from dagster.core.selector.subset_selector import parse_clause
from dagster.core.definitions.config import ConfigMapping

if TYPE_CHECKING:
    from dagster.core.asset_defs import AssetsDefinition, SourceAsset
    from dagster.core.asset_defs.asset_selection import AssetSelection
    from dagster.core.definitions import (
        JobDefinition,
        PartitionsDefinition,
        PartitionSetDefinition,
        PartitionedConfig,
    )


class UnresolvedAssetJobDefinition(
    NamedTuple(
        "_UnresolvedAssetJobDefinition",
        [
            ("name", str),
            ("selection", "AssetSelection"),
            ("config", Optional[Union[ConfigMapping, Dict[str, Any], "PartitionedConfig"]]),
            ("description", Optional[str]),
            ("tags", Optional[Dict[str, Any]]),
            ("partitions_def", Optional["PartitionsDefinition"]),
        ],
    )
):
    def __new__(
        cls,
        name: str,
        selection: "AssetSelection",
        config: Optional[Union[ConfigMapping, Dict[str, Any], "PartitionedConfig"]] = None,
        description: Optional[str] = None,
        tags: Optional[Dict[str, Any]] = None,
        partitions_def: Optional["PartitionsDefinition"] = None,
    ):
        from dagster.core.asset_defs.asset_selection import AssetSelection
        from dagster.core.definitions import PartitionsDefinition

        return super(UnresolvedAssetJobDefinition, cls).__new__(
            cls,
            name=check.str_param(name, "name"),
            selection=check.inst_param(selection, "selection", AssetSelection),
            config=config,
            description=check.opt_str_param(description, "description"),
            tags=check.opt_dict_param(tags, "tags"),
            partitions_def=check.opt_inst_param(
                partitions_def, "partitions_def", PartitionsDefinition
            ),
        )

    def get_partition_set_def(self):
        from dagster.core.definitions import PartitionSetDefinition

        if self.partitions_def is None:
            return None

        return PartitionSetDefinition(
            job_name=self.name,
            name=f"{self.name}_partition_set",
            partitions_def=self.partitions_def,
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
            config=self.config,
            source_assets=source_assets,
            description=self.description,
            tags=self.tags,
            asset_selection=self.selection.resolve(assets),
            partitions_def=self.partitions_def,
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
    selection: Optional[Union[str, Sequence[str], "AssetSelection"]] = None,
    config: Optional[Union[ConfigMapping, Dict[str, Any], "PartitionedConfig"]] = None,
    description: Optional[str] = None,
    tags: Optional[Dict[str, Any]] = None,
    partitions_def: Optional["ParitionsDefinition"] = None,
) -> UnresolvedAssetJobDefinition:
    """Creates a definition of a job which will materialize a selection of assets. This will only be
    resolved to a JobDefinition once placed in a repository.

    Args:
        name (str):
            The name for the Job.
        selection (Union[str, Sequence[str], AssetSelection]):
            A selection over the set of Assets available on your repository. This can be a string
            such as "my_asset*", a list of such strings (representing a union of these selections),
            or an AssetSelection object.

            This selection will be resolved to a set of Assets once the repository is loaded with a
            set of AssetsDefinitions.
        config:
            Describes how the Job is parameterized at runtime.

            If no value is provided, then the schema for the job's run config is a standard
            format based on its solids and resources.

            If a dictionary is provided, then it must conform to the standard config schema, and
            it will be used as the job's run config for the job whenever the job is executed.
            The values provided will be viewable and editable in the Dagit playground, so be
            careful with secrets.

            If a :py:class:`ConfigMapping` object is provided, then the schema for the job's run config is
            determined by the config mapping, and the ConfigMapping, which should return
            configuration in the standard format to configure the job.

            If a :py:class:`PartitionedConfig` object is provided, then it defines a discrete set of config
            values that can parameterize the job, as well as a function for mapping those
            values to the base config. The values provided will be viewable and editable in the
            Dagit playground, so be careful with secrets.
        tags (Optional[Mapping[str, Any]]):
            Arbitrary information that will be attached to the execution of the Job.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        description (Optional[str]):
            A description for the Job.
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
        config=config,
        description=description,
        tags=tags,
        partitions_def=partitions_def,
    )
