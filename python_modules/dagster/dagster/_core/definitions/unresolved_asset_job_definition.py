import operator
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, NamedTuple, Optional, Sequence, Union, cast

import dagster._check as check
from dagster._core.definitions import AssetKey
from dagster._core.definitions.run_request import RunRequest
from dagster._core.selector.subset_selector import parse_clause

from .asset_layer import build_asset_selection_job
from .config import ConfigMapping

if TYPE_CHECKING:
    from dagster._core.definitions import (
        AssetSelection,
        AssetsDefinition,
        ExecutorDefinition,
        JobDefinition,
        PartitionSetDefinition,
        PartitionedConfig,
        PartitionsDefinition,
        SourceAsset,
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
            ("executor_def", Optional["ExecutorDefinition"]),
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
        executor_def: Optional["ExecutorDefinition"] = None,
    ):
        from dagster._core.definitions import (
            AssetSelection,
            ExecutorDefinition,
            PartitionsDefinition,
        )

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
            executor_def=check.opt_inst_param(executor_def, "partitions_def", ExecutorDefinition),
        )

    def get_partition_set_def(self) -> Optional["PartitionSetDefinition"]:
        from dagster._core.definitions import PartitionSetDefinition, PartitionedConfig

        if self.partitions_def is None:
            return None

        partitioned_config = self.config if isinstance(self.config, PartitionedConfig) else None

        tags_fn = (
            partitioned_config
            and partitioned_config.tags_for_partition_fn
            or (lambda _: cast(Dict[str, str], {}))
        )
        run_config_fn = (
            partitioned_config
            and partitioned_config.run_config_for_partition_fn
            or (lambda _: cast(Dict[str, str], {}))
        )
        return PartitionSetDefinition(
            job_name=self.name,
            name=f"{self.name}_partition_set",
            partitions_def=self.partitions_def,
            run_config_fn_for_partition=run_config_fn,
            tags_fn_for_partition=tags_fn,
        )

    def run_request_for_partition(
        self,
        partition_key: str,
        run_key: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None,
        asset_selection: Optional[Sequence[AssetKey]] = None,
    ) -> RunRequest:
        """
        Creates a RunRequest object for a run that processes the given partition.

        Args:
            partition_key: The key of the partition to request a run for.
            run_key (Optional[str]): A string key to identify this launched run. For sensors, ensures that
                only one run is created per run key across all sensor evaluations.  For schedules,
                ensures that one run is created per tick, across failure recoveries. Passing in a `None`
                value means that a run will always be launched per evaluation.
            tags (Optional[Dict[str, str]]): A dictionary of tags (string key-value pairs) to attach
                to the launched run.

        Returns:
            RunRequest: an object that requests a run to process the given partition.
        """
        partition_set = self.get_partition_set_def()
        if not partition_set:
            check.failed("Called run_request_for_partition on a non-partitioned job")

        partition = partition_set.get_partition(partition_key)
        run_config = partition_set.run_config_for_partition(partition)
        run_request_tags = (
            {**tags, **partition_set.tags_for_partition(partition)}
            if tags
            else partition_set.tags_for_partition(partition)
        )

        return RunRequest(
            run_key=run_key,
            run_config=run_config,
            tags=run_request_tags,
            asset_selection=asset_selection,
        )

    def resolve(
        self,
        assets: Sequence["AssetsDefinition"],
        source_assets: Sequence["SourceAsset"],
        default_executor_def: Optional["ExecutorDefinition"] = None,
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
            asset_selection=self.selection.resolve([*assets, *source_assets]),
            partitions_def=self.partitions_def,
            executor_def=self.executor_def or default_executor_def,
        )


def _selection_from_string(string: str) -> "AssetSelection":
    from dagster._core.definitions import AssetSelection

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
    partitions_def: Optional["PartitionsDefinition"] = None,
    executor_def: Optional["ExecutorDefinition"] = None,
) -> UnresolvedAssetJobDefinition:
    """Creates a definition of a job which will materialize a selection of assets. This will only be
    resolved to a JobDefinition once placed in a repository.

    Args:
        name (str):
            The name for the job.
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
        tags (Optional[Mapping[str, Any]]):
            Arbitrary information that will be attached to the execution of the Job.
            Values that are not strings will be json encoded and must meet the criteria that
            `json.loads(json.dumps(value)) == value`.  These tag values may be overwritten by tag
            values provided at invocation time.
        description (Optional[str]):
            A description for the Job.
        partitions_def (Optional[PartitionsDefinition]):
            Defines the set of partitions for this job. All AssetDefinitions selected for this job
            must have a matching PartitionsDefinition.
        executor_def (Optional[ExecutorDefinition]):
            How this Job will be executed. Defaults to :py:class:`multi_or_in_process_executor`,
            which can be switched between multi-process and in-process modes of execution. The
            default mode of execution is multi-process.


    Returns:
        UnresolvedAssetJobDefinition: The job, which can be placed inside a repository.

    Examples:

        .. code-block:: python

            # A job that targets all assets in the repository:
            @asset
            def asset1():
                ...

            @repository
            def repo():
                return [asset1, define_asset_job("all_assets")]

            # A job that targets all the assets in a group:
            @repository
            def repo():
                return [
                    assets,
                    define_asset_job("marketing_job", selection=AssetSelection.groups("marketing")),
                ]

            # Resources are supplied to the assets, not the job:
            @asset(required_resource_keys={"slack_client"})
            def asset1():
                ...

            @repository
            def prod_repo():
                return [
                    *with_resources([asset1], resource_defs={"slack_client": prod_slack_client}),
                    define_asset_job("all_assets"),
                ]
    """
    from dagster._core.definitions import AssetSelection

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
        executor_def=executor_def,
    )
