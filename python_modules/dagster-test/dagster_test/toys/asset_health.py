from datetime import timedelta

import dagster as dg
from dagster._core.definitions.freshness import InternalFreshnessPolicy
from dagster._time import get_current_timestamp


def should_fail(logger):
    now = get_current_timestamp()
    logger.info(f"Current timestamp: {int(now)}")
    if int(now) % 2 == 0:
        return False
    return True


@dg.asset
def random_1(context):
    if should_fail(context.log):
        raise Exception("random_1 failed")
    return 1


@dg.asset
def random_2(context, random_1):
    if should_fail(context.log):
        raise Exception("random_2 failed")
    return 1


@dg.asset
def random_3(context, random_1):
    if should_fail(context.log):
        raise Exception("random_3 failed")
    return 1


@dg.asset
def always_materializes():
    return 1


@dg.asset
def always_fails():
    raise Exception("always_fails failed")


@dg.asset(output_required=False)
def always_skips():
    if False:
        yield dg.Output(1)


@dg.asset(output_required=False)
def sometimes_skips(context):
    # if should_fail is True twice, fail the asset. If true once, skip the asset. If false, materialize the asset.
    if should_fail(context.log):
        if should_fail(context.log):
            raise Exception("sometimes_skips failed")
    else:
        yield dg.Output(1)


static_partitions = dg.StaticPartitionsDefinition(
    ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
)


@dg.asset(partitions_def=static_partitions, output_required=False)
def always_skips_partitioned():
    if False:
        yield dg.Output(1)


@dg.asset(partitions_def=static_partitions)
def random_failure_partitioned_asset(context):
    if should_fail(context.log):
        raise Exception("partitioned_asset failed")
    return 1


@dg.asset_check(asset=random_1)
def random_1_check_always_warns():
    return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)


@dg.asset_check(asset=random_1)
def random_1_check_always_errors():
    return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.ERROR)


@dg.asset_check(asset=random_1)
def random_1_check_always_execution_fails():
    raise Exception("failed!")


@dg.op
def observe_random_1(context):
    context.log_event(dg.AssetObservation(asset_key="random_1", metadata={"foo": "bar"}))


@dg.job
def observe_random_1_job():
    observe_random_1()


@dg.asset_check(asset=random_2)
def random_2_check_sometimes_warns(context):
    if should_fail(context.log):
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=random_2)
def random_2_check_sometimes_errors(context):
    if should_fail(context.log):
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.ERROR)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=always_materializes)
def always_materializes_check_sometimes_warns(context):
    if should_fail(context.log):
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=always_materializes)
def always_materializes_check_sometimes_errors(context):
    if should_fail(context.log):
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.ERROR)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.observable_source_asset
def observable_source_asset_always_observes():
    return dg.DataVersion("5")


@dg.observable_source_asset
def observable_source_asset_execution_error():
    raise Exception("failed!")


@dg.observable_source_asset
def observable_source_asset_random_execution_error(context):
    if should_fail(context.log):
        raise Exception("failed!")

    return dg.DataVersion("5")


@dg.asset(
    freshness_policy=InternalFreshnessPolicy.time_window(
        fail_window=timedelta(minutes=5), warn_window=timedelta(minutes=1)
    )
)
def asset_with_freshness_and_warning():
    return 1


source_asset = dg.SourceAsset("source_asset")


@dg.asset_check(asset=source_asset)
def source_asset_check():
    return dg.AssetCheckResult(passed=True)


@dg.op
def insert_source_asset_materializations(context: dg.OpExecutionContext) -> None:
    context.log_event(dg.AssetMaterialization(source_asset.key))


@dg.job
def insert_source_asset_materializations_job() -> None:
    insert_source_asset_materializations()


# jobs for reporting observations and materializations for assets that do not have definitions in dagster
@dg.op
def observe_no_def_observable(context):
    context.log_event(dg.AssetObservation(asset_key="no_def_observable", metadata={"foo": "bar"}))


@dg.job
def observe_no_def_observable_job():
    observe_no_def_observable()


@dg.op
def materialize_no_def_materializable(context):
    context.log_event(
        dg.AssetMaterialization(
            asset_key="no_def_materializable", metadata={"foo": "bar"}, partition="1"
        )
    )
    context.log_event(
        dg.AssetMaterialization(
            asset_key="no_def_materializable", metadata={"foo": "bar"}, partition="2"
        )
    )
    context.log_event(
        dg.AssetMaterialization(
            asset_key="no_def_materializable", metadata={"foo": "bar"}, partition="4"
        )
    )


@dg.op
def checks_no_def_materializable(context):
    context.log_event(
        dg.AssetCheckEvaluation(
            passed=True,
            asset_key=dg.AssetKey("no_def_materializable"),
            check_name="check_for_no_def_materializable",
        )
    )


@dg.job
def materialize_no_def_materializable_job():
    materialize_no_def_materializable()
    checks_no_def_materializable()


random_assets_job = dg.define_asset_job(
    "random_assets_job", selection=dg.AssetSelection.assets(random_1, random_2, random_3)
)

random_assets_every_15m_schedule = dg.ScheduleDefinition(
    job=random_assets_job,
    cron_schedule="*/15 * * * *",
)


def get_assets_and_checks():
    return [
        random_1,
        random_2,
        random_3,
        always_materializes,
        always_fails,
        random_failure_partitioned_asset,
        random_1_check_always_warns,
        random_1_check_always_errors,
        random_1_check_always_execution_fails,
        random_2_check_sometimes_warns,
        random_2_check_sometimes_errors,
        always_materializes_check_sometimes_warns,
        always_materializes_check_sometimes_errors,
        observable_source_asset_always_observes,
        observable_source_asset_execution_error,
        observable_source_asset_random_execution_error,
        asset_with_freshness_and_warning,
        observe_random_1_job,
        source_asset,
        source_asset_check,
        insert_source_asset_materializations_job,
        materialize_no_def_materializable_job,
        observe_no_def_observable_job,
        random_assets_job,
        random_assets_every_15m_schedule,
        always_skips,
        sometimes_skips,
        always_skips_partitioned,
    ]
