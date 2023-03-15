import math
import time
from typing import Optional

from dagster import Definitions, asset
from dagster._core.definitions.assets import AssetsDefinition
from dagster._core.definitions.events import AssetKey, AssetMaterialization
from dagster._core.definitions.metadata import TextMetadataValue
from dagster._core.events.log import EventLogEntry
from dagster._core.instance import DagsterInstance
from dagster._core.storage.branching.branching_io_manager import BranchingIOManager

from .utils import AssetBasedInMemoryIOManager, DefinitionsRunner


@asset
def now_time() -> int:
    return int(math.floor(time.time() * 100))


def get_now_time_plus_N(N: int) -> AssetsDefinition:
    @asset
    def now_time_plus_N(now_time: int) -> int:
        return now_time + N

    return now_time_plus_N


@asset
def now_time_plus_20_after_plus_N(now_time_plus_N: int) -> int:
    return now_time_plus_N + 20


def test_basic_bound_runner_usage():
    with DefinitionsRunner.ephemeral(
        Definitions(
            assets=[now_time],
            resources={"io_manager": AssetBasedInMemoryIOManager()},
        ),
    ) as runner:
        assert runner.materialize_all_assets().success
        assert isinstance(runner.load_asset_value("now_time"), int)


def get_env_entry(
    event_log_entry: EventLogEntry, metadata_key="io_manager_branch"
) -> Optional[str]:
    asset_mat = event_log_entry.asset_materialization
    return (
        get_branch_name_from_materialization(asset_mat, metadata_key=metadata_key)
        if asset_mat
        else None
    )


def get_branch_name_from_materialization(
    asset_materialization: AssetMaterialization, metadata_key="io_manager_branch"
) -> Optional[str]:
    entry = asset_materialization.metadata.get(metadata_key)
    if isinstance(entry, TextMetadataValue):
        return entry.value
    else:
        return None


def test_write_staging_label():
    with DefinitionsRunner.ephemeral(
        Definitions(
            assets=[now_time],
            resources={
                "io_manager": BranchingIOManager(
                    parent_io_manager=AssetBasedInMemoryIOManager(),
                    branch_io_manager=AssetBasedInMemoryIOManager(),
                )
            },
        ),
    ) as staging_runner:
        assert staging_runner.materialize_all_assets().success

        all_mat_log_records = staging_runner.get_all_asset_materialization_event_records("now_time")
        assert all_mat_log_records

        assert len(all_mat_log_records) == 1
        asset_mat = all_mat_log_records[0].event_log_entry.asset_materialization

        assert asset_mat
        assert get_branch_name_from_materialization(asset_mat) == "dev"


def test_write_alternative_branch_metadata_key():
    with DefinitionsRunner.ephemeral(
        Definitions(
            assets=[now_time],
            resources={
                "io_manager": BranchingIOManager(
                    parent_io_manager=AssetBasedInMemoryIOManager(),
                    branch_io_manager=AssetBasedInMemoryIOManager(),
                    branch_metadata_key="another_key",
                ),
            },
        ),
    ) as staging_runner:
        assert staging_runner.materialize_all_assets()

        all_mat_log_records = staging_runner.get_all_asset_materialization_event_records("now_time")
        assert all_mat_log_records

        assert len(all_mat_log_records) == 1
        asset_mat = all_mat_log_records[0].event_log_entry.asset_materialization

        assert asset_mat
        assert get_branch_name_from_materialization(asset_mat, metadata_key="another_key") == "dev"


def test_basic_workflow():
    """
    In this test we are going to iterate on an asset in the middle of a graph.

    now_time --> now_time_plus_N --> now_time_plus_20_after_plus_N

    We are going to iterate on and change the logic of now_time_plus_N in staging and confirm
    that prod is untouched
    """
    with DagsterInstance.ephemeral() as prod_instance, DagsterInstance.ephemeral() as dev_instance:
        now_time_plus_N_actually_10 = get_now_time_plus_N(10)

        prod_io_manager = AssetBasedInMemoryIOManager()
        dev_io_manager = AssetBasedInMemoryIOManager()

        prod_runner = DefinitionsRunner(
            Definitions(
                assets=[now_time, now_time_plus_N_actually_10, now_time_plus_20_after_plus_N],
                resources={"io_manager": prod_io_manager},
            ),
            prod_instance,
        )

        dev_t0_runner = DefinitionsRunner(
            Definitions(
                assets=[now_time, now_time_plus_N_actually_10, now_time_plus_20_after_plus_N],
                resources={
                    "io_manager": BranchingIOManager(
                        parent_io_manager=prod_io_manager,
                        branch_io_manager=dev_io_manager,
                    )
                },
            ),
            dev_instance,
        )

        assert prod_runner.materialize_all_assets()

        now_time_prod_mat_1 = prod_instance.get_latest_materialization_event(AssetKey("now_time"))
        assert now_time_prod_mat_1
        assert not get_env_entry(now_time_prod_mat_1)  # should be no env entry
        now_time_prod_value_1 = prod_runner.load_asset_value("now_time")
        assert isinstance(now_time_prod_value_1, int)

        # We have materialized all the prod assets. Imagine this took a very long time.
        # Now I want to iterate on a the now_time_plus_N asset in staging. First run with its existing definition

        assert dev_t0_runner.materialize_asset("now_time_plus_N").success

        all_mat_event_log_records = dev_t0_runner.get_all_asset_materialization_event_records(
            "now_time_plus_N"
        )

        assert all_mat_event_log_records
        assert len(all_mat_event_log_records) == 1
        now_plus_15_mat_1_log_record = all_mat_event_log_records[0]
        assert get_env_entry(now_plus_15_mat_1_log_record.event_log_entry) == "dev"
        # we have affirmed that this latest materialization for now_plus_15_mat_1 is in staging

        assert dev_t0_runner.load_asset_value("now_time_plus_N") == now_time_prod_value_1 + 10

        # we have done this with *no* materializations of the root asset in staging
        assert not dev_t0_runner.get_all_asset_materialization_event_records("now_time")

        dev_t1_runner = DefinitionsRunner(
            Definitions(
                # redefining now_time_plus_N to add 17 rather than 10
                assets=[now_time, get_now_time_plus_N(17), now_time_plus_20_after_plus_N],
                resources={
                    "io_manager": BranchingIOManager(
                        parent_io_manager=prod_io_manager,
                        branch_io_manager=dev_io_manager,
                    )
                },
            ),
            dev_instance,
        )

        # now we materialize the modified staging asset using upstream prod and confirm that
        # new calculation holds
        dev_t1_runner.materialize_asset("now_time_plus_N")

        result = dev_t1_runner.load_asset_value("now_time_plus_N")

        assert (
            # staging_after_iteration_runner.load_asset_value("now_time_plus_N")
            result
            == now_time_prod_value_1 + 17
        )

        # we were able to do this without having an materializations in staging of the root asset
        assert not dev_t1_runner.get_all_asset_materialization_event_records("now_time")

        dev_t1_runner.materialize_asset("now_time_plus_20_after_plus_N")

        # downstream gets it from staging
        assert dev_t1_runner.load_asset_value("now_time_plus_20_after_plus_N") == (
            now_time_prod_value_1 + 17 + 20
        )
