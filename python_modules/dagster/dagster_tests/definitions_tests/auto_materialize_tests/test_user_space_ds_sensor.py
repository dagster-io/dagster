from typing import Iterable, Mapping, NamedTuple, Optional, Sequence, Set

from dagster import (
    Definitions,
    _check as check,
    asset,
)
from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_daemon_cursor import AssetDaemonCursor
from dagster._core.definitions.asset_dep import CoercibleToAssetDep
from dagster._core.definitions.asset_key import CoercibleToAssetKey
from dagster._core.definitions.declarative_scheduling.ds_sensor import DSSensorDefinition
from dagster._core.definitions.declarative_scheduling.scheduling_condition import (
    SchedulingCondition,
)
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.materialize import materialize
from dagster._core.definitions.metadata import ArbitraryMetadataMapping
from dagster._core.definitions.run_request import RunRequest, SensorResult
from dagster._core.definitions.sensor_definition import build_sensor_context
from dagster._core.instance import DagsterInstance
from dagster._daemon.asset_daemon import (
    asset_daemon_cursor_from_instigator_serialized_cursor,
    asset_daemon_cursor_to_instigator_serialized_cursor,
)


def ds_asset(
    *,
    deps: Optional[Iterable[CoercibleToAssetDep]] = None,
    description: Optional[str] = None,
    metadata: Optional[ArbitraryMetadataMapping] = None,
    group_name: Optional[str] = None,
    code_version: Optional[str] = None,
    key: Optional[CoercibleToAssetKey] = None,
    scheduling: Optional[SchedulingCondition] = None,
    check_specs: Optional[Sequence[AssetCheckSpec]] = None,
    owners: Optional[Sequence[str]] = None,
    tags: Optional[Mapping[str, str]] = None,
):
    return asset(
        key=key,
        deps=deps,
        description=description,
        metadata=metadata,
        group_name=group_name,
        code_version=code_version,
        auto_materialize_policy=(scheduling.as_auto_materialize_policy() if scheduling else None),
        check_specs=check_specs,
        owners=owners,
        tags=tags,
    )


class DSSensorResult(NamedTuple):
    sensor_result: SensorResult
    asset_daemon_cursor: AssetDaemonCursor

    @property
    def run_requests(self) -> Sequence[RunRequest]:
        return self.sensor_result.run_requests or []


def asset_key_strs(run_request: RunRequest) -> Set[str]:
    return {asset_key.to_user_string() for asset_key in (run_request.asset_selection or [])}


def asset_key_str(run_request: RunRequest) -> str:
    aks = asset_key_strs(run_request)
    assert len(aks) == 1
    return next(iter(aks))


def pulse_ds_sensor(
    sensor_def: DSSensorDefinition,
    instance: DagsterInstance,
    defs: Definitions,
    prev_cursor: AssetDaemonCursor,
) -> DSSensorResult:
    repository_def = defs.get_repository_def()
    sensor_context = build_sensor_context(
        instance=instance,
        repository_def=repository_def,
        cursor=asset_daemon_cursor_to_instigator_serialized_cursor(prev_cursor),
        sensor_name=sensor_def.name,
    )
    result = sensor_def(sensor_context)

    assert isinstance(result, SensorResult)

    for run_request in result.run_requests or []:
        if not run_request.asset_selection:
            continue

        job_def = (
            repository_def.get_job(run_request.job_name)
            if run_request.job_name
            else check.inst(
                repository_def.get_implicit_job_def_for_assets(run_request.asset_selection),
                JobDefinition,
            )
        )

        assert job_def.execute_in_process(instance=instance).success

    return DSSensorResult(
        sensor_result=result,
        asset_daemon_cursor=asset_daemon_cursor_from_instigator_serialized_cursor(
            serialized_cursor=result.cursor, asset_graph=repository_def.asset_graph
        ),
    )


def test_evaluate_empty_basic_ds_sensor() -> None:
    @ds_asset(scheduling=SchedulingCondition.eager_with_rate_limit())
    def an_asset() -> None: ...

    sensor_def = DSSensorDefinition(
        name="test_sensor",
        asset_selection="*",
    )

    defs = Definitions(assets=[an_asset], sensors=[sensor_def])

    instance = DagsterInstance.ephemeral()

    ds_result_1 = pulse_ds_sensor(
        sensor_def=sensor_def,
        instance=instance,
        defs=defs,
        prev_cursor=AssetDaemonCursor.empty(),
    )

    assert isinstance(ds_result_1, DSSensorResult)
    assert len(ds_result_1.run_requests) == 1
    assert asset_key_str(ds_result_1.run_requests[0]) == "an_asset"

    ds_result_2 = pulse_ds_sensor(
        sensor_def=sensor_def,
        instance=instance,
        defs=defs,
        prev_cursor=ds_result_1.asset_daemon_cursor,
    )

    assert isinstance(ds_result_2, DSSensorResult)
    assert len(ds_result_2.run_requests) == 0


def test_eval_upstream_of_eager() -> None:
    @ds_asset()
    def upstream() -> None: ...

    @ds_asset(deps=[upstream], scheduling=SchedulingCondition.eager_with_rate_limit())
    def downstream() -> None: ...

    sensor_def = DSSensorDefinition(
        name="test_sensor",
        asset_selection="downstream",
    )

    defs = Definitions(assets=[upstream, downstream], sensors=[sensor_def])

    instance = DagsterInstance.ephemeral()

    assert materialize(assets=[upstream, downstream], instance=instance).success

    ds_result_1 = pulse_ds_sensor(
        sensor_def=sensor_def,
        instance=instance,
        defs=defs,
        prev_cursor=AssetDaemonCursor.empty(),
    )

    assert isinstance(ds_result_1, DSSensorResult)
    assert len(ds_result_1.run_requests) == 0

    return

    ds_result_2 = pulse_ds_sensor(
        sensor_def=sensor_def,
        instance=instance,
        defs=defs,
        prev_cursor=ds_result_1.asset_daemon_cursor,
    )

    assert isinstance(ds_result_2, DSSensorResult)
    assert len(ds_result_2.run_requests) == 0
