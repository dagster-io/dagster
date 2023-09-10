from dagster import AssetExecutionContext, OpExecutionContext, asset, materialize


def test_base_asset_execution_context() -> None:
    passed = {"called": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        passed["called"] = True

    assert materialize([an_asset]).success
    assert passed["called"]


def test_isinstance_op_execution_context_asset_execution_context() -> None:
    passed = {"called": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        passed["called"] = True

    assert materialize([an_asset]).success
    assert passed["called"]
