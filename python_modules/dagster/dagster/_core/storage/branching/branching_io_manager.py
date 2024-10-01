from typing import Any, Optional

from dagster import InputContext, OutputContext
from dagster._config.pythonic_config import ConfigurableIOManager, ResourceDependency
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.metadata import TextMetadataValue
from dagster._core.event_api import AssetRecordsFilter
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.storage.io_manager import IOManager


def get_text_metadata_value(materialization: AssetMaterialization, key: str) -> Optional[str]:
    metadata_value = materialization.metadata.get(key)
    return metadata_value.value if isinstance(metadata_value, TextMetadataValue) else None


def latest_materialization_log_entry(
    instance: DagsterInstance, asset_key: AssetKey, partition_key: Optional[str] = None
) -> Optional[EventLogEntry]:
    event_records = instance.fetch_materializations(
        AssetRecordsFilter(
            asset_key=asset_key,
            asset_partitions=[partition_key] if partition_key else None,
        ),
        limit=1,
    ).records
    return event_records[0].event_log_entry if event_records else None


class BranchingIOManager(ConfigurableIOManager):
    """A branching I/O manager composes two I/O managers.

    1) The parent I/O manager, typically your production environment.
    2) The branch I/O manager, typically a development or branched environment.

    The objective of this to allow a developer to safely read from a production
    environment and then write to a separate development environment. Once data
    has been written to the branch environment subsequent reads of that asset
    are sourced from the branch environment. This bookkeeping is done in Dagster's
    asset catalog by emitting AssetMaterializations with metadata.

    This is designed for iterative development on asset graphs, especially
    where assets early in the graph are large and expensive to compute. One can
    iteratively develop on downstream assets in that graph safely.

    Some storage systems branching functionality natively. Examples include Snowflake's
    CLONE feature. Branching I/O managers allow users to implement that functionality
    in more flexible software layer over arbitrary storage systems.
    """

    parent_io_manager: ResourceDependency[IOManager]
    branch_io_manager: ResourceDependency[IOManager]

    branch_name: str = "dev"
    branch_metadata_key: str = "io_manager_branch"

    def load_input(self, context: InputContext) -> Any:
        if not context.has_asset_key:
            # we are dealing with an op input
            # just load it with the branch manager
            return self.branch_io_manager.load_input(context)
        else:
            # we are dealing with an asset input
            # figure out which partition keys are loaded, if any
            partition_keys = []
            if context.has_asset_partitions:
                partition_keys = context.asset_partition_keys

            # we'll fetch materializations with key=None if we aren't loading
            # a partitioned asset, this will return us the latest materialization
            # of an unpartitioned asset
            if len(partition_keys) == 0:
                partition_keys = [None]

            # grab the latest materialization for each partition that we
            # need to load, OR just the latest materialization if not partitioned
            event_log_entries = [
                latest_materialization_log_entry(
                    instance=context.instance,
                    asset_key=context.asset_key,
                    partition_key=partition_key,
                )
                for partition_key in partition_keys
            ]

            # if all partitions are available in the branch, we can load from the branch
            # otherwise we need to load from the parent
            if all(
                event_log_entry is not None
                and event_log_entry.asset_materialization
                and get_text_metadata_value(
                    event_log_entry.asset_materialization, self.branch_metadata_key
                )
                == self.branch_name
                for event_log_entry in event_log_entries
            ):
                context.log.info(
                    f'Branching Manager: Loading "{context.asset_key.to_user_string()}" from'
                    f' "{self.branch_name}"'
                )
                return self.branch_io_manager.load_input(context)

            context.log.info(
                f'Branching Manager Loading "{context.asset_key.to_user_string()}" from parent'
            )
            return self.parent_io_manager.load_input(context)

    def handle_output(self, context: OutputContext, obj: Any) -> None:
        # always write to the branch manager
        self.branch_io_manager.handle_output(context, obj)

        if context.has_asset_key:
            # we are dealing with an asset output (not an op output)
            # mark the asset materialization with the branch name
            context.add_output_metadata({self.branch_metadata_key: self.branch_name})
            context.log.info(
                f'Branching Manager: Writing "{context.asset_key.to_user_string()}" to branch'
                f' "{self.branch_name}"'
            )
