import dagster as dg
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


static_partitions = dg.StaticPartitionsDefinition(
    ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"]
)


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
    ]
