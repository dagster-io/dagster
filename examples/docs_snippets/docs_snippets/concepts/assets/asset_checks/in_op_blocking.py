from dagster import AssetCheckResult, AssetCheckSpec, Output, asset


class ExampleException(Exception):
    pass


@asset(check_specs=[AssetCheckSpec(name="foo", asset="my_asset")])
def my_asset():
    yield Output("foo")

    passed = False
    yield AssetCheckResult(passed=passed)

    if not passed:
        raise ExampleException()


@asset
def downstream_asset(my_asset):
    pass
