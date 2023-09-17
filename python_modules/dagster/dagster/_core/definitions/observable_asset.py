from typing import Optional, Sequence

from dagster import _check as check
from dagster._core.definitions.asset_spec import (
    SYSTEM_METADATA_KEY_ASSET_VARIETAL,
    AssetSpec,
    AssetVarietal,
    ObservableAssetSpec,
)
from dagster._core.definitions.decorators.asset_decorator import asset, multi_asset
from dagster._core.definitions.events import AssetMaterialization, AssetObservation
from dagster._core.definitions.source_asset import SourceAsset
from dagster._core.events import (
    AssetObservationData,
    DagsterEvent,
    DagsterEventType,
    EventSpecificData,
    StepMaterializationData,
)
from dagster._core.instance import DagsterInstance


def create_unexecutable_observable_assets_def(specs: Sequence[ObservableAssetSpec]):
    @multi_asset(
        specs=[
            AssetSpec(
                key=spec.key,
                description=spec.description,
                group_name=spec.group_name,
                metadata={
                    **(spec.metadata or {}),
                    **{SYSTEM_METADATA_KEY_ASSET_VARIETAL: AssetVarietal.UNEXECUTABLE.value},
                },
                deps=[dep.asset_key for dep in spec.deps],
            )
            for spec in specs
        ]
    )
    def an_asset() -> None:
        keys = [spec.key for spec in specs]
        raise NotImplementedError(
            f"Asset {keys} is not executable. This is an internal framework error and should have"
            " been caught earlier."
        )

    return an_asset


# Our internal guts can handle empty strings for job name and run id
# However making thse named constants for documentation, to encode where we are making the assumption,
# and to allow us to change this more easily in the future, provided we are disciplined about
# actually using this constants.
RUNLESS_JOB_NAME = ""
RUNLESS_RUN_ID = ""


def report_runless_event(
    instance: DagsterInstance, event_type: DagsterEventType, event_specific_data: EventSpecificData
) -> None:
    dagster_event = DagsterEvent(
        event_type_value=event_type.value,
        job_name=RUNLESS_JOB_NAME,
        event_specific_data=event_specific_data,
    )

    instance.report_dagster_event(dagster_event=dagster_event, run_id=RUNLESS_RUN_ID)


def report_runless_asset_materialization(
    asset_materialization: AssetMaterialization,
    instance: Optional[DagsterInstance] = None,
) -> None:
    report_runless_event(
        instance or DagsterInstance.get(),
        DagsterEventType.ASSET_MATERIALIZATION,
        StepMaterializationData(asset_materialization),
    )


def report_runless_asset_observation(
    asset_observation: AssetObservation,
    instance: Optional[DagsterInstance] = None,
) -> None:
    report_runless_event(
        instance or DagsterInstance.get(),
        DagsterEventType.ASSET_OBSERVATION,
        AssetObservationData(asset_observation),
    )


def create_unexecutable_observable_assets_def_from_source_asset(source_asset: SourceAsset):
    check.invariant(
        source_asset.observe_fn is None,
        "Observable source assets not supported yet: observe_fn should be None",
    )
    check.invariant(
        source_asset.partitions_def is None,
        "Observable source assets not supported yet: partitions_def should be None",
    )
    check.invariant(
        source_asset.auto_observe_interval_minutes is None,
        "Observable source assets not supported yet: auto_observe_interval_minutes should be none",
    )

    kwargs = {
        "key": source_asset.key,
        "metadata": {**source_asset.metadata, **{SYSTEM_METADATA_KEY_ASSET_VARIETAL: AssetVarietal.UNEXECUTABLE.value}},
        "group_name": source_asset.group_name,
        "description": source_asset.description,
    }

    if source_asset.io_manager_def:
        kwargs["io_manager_def"] = source_asset.io_manager_def
    elif source_asset.io_manager_key:
        kwargs["io_manager_key"] = source_asset.io_manager_key

    @asset(**kwargs)
    def shim_asset() -> None:
        raise NotImplementedError(f"Asset {source_asset.key} is not executable")

    return shim_asset
