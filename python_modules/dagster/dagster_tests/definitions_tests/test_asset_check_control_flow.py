from dagster import AssetCheckDep, AssetCheckResult, AssetCheckSeverity, asset, asset_check


def test_if_check_fails_then_skip_downstream_and_show_error_state_on_asset():
    @asset_check(asset="asset1", blocking=True)
    def check1():
        return AssetCheckResult.error()


def test_non_blocking_warn():
    @asset_check(asset="asset1")
    def check1():
        return AssetCheckResult.warn()


def test_non_blocking_error():
    @asset_check(asset="asset1")
    def check1():
        return AssetCheckResult.error()


def test_dont_run_downstream_until_check_finishes_but_still_run_downstream_even_if_check_fails():
    # note: not clear to me that we should support this, given that we don't support it for asset
    # dependencies
    @asset_check(asset="asset1")
    def check1():
        return AssetCheckResult.error(skip_downstream=False)


def test_some_downstream_assets_want_to_skip_on_failure_others_dont():
    @asset_check(asset="asset1")
    def check1():
        return AssetCheckResult.error()

    @asset(deps=["asset1", AssetCheckDep(check1, skip_on=[AssetCheckSeverity.ERROR])])
    def asset2():
        ...

    @asset(deps=["asset1"])
    def asset3():
        ...


def test_what_happens_if_blocking_and_issues_warn():
    # does the downstream get skipped in this case? seems a little ambiguous
    @asset_check(asset="asset1", blocking=True)
    def check1():
        return AssetCheckResult.warn()
