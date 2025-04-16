import random

import dagster as dg


@dg.asset
def random_1():
    if random.random() < 0.5:
        raise Exception("random_1 failed")
    return 1


@dg.asset
def random_2(random_1):
    if random.random() < 0.5:
        raise Exception("random_2 failed")
    return 1


@dg.asset
def random_3(random_1):
    if random.random() < 0.5:
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
def random_failure_partitioned_asset():
    if random.random() < 0.5:
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
def random_2_check_sometimes_warns():
    if random.random() < 0.5:
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=random_2)
def random_2_check_sometimes_errors():
    if random.random() < 0.5:
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.ERROR)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=always_materializes)
def always_materializes_check_sometimes_warns():
    if random.random() < 0.5:
        return dg.AssetCheckResult(passed=False, severity=dg.AssetCheckSeverity.WARN)
    else:
        return dg.AssetCheckResult(passed=True)


@dg.asset_check(asset=always_materializes)
def always_materializes_check_sometimes_errors():
    if random.random() < 0.5:
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
    ]
