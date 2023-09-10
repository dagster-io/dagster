from dagster import AssetExecutionContext, OpExecutionContext, asset, job, materialize, op


def test_base_asset_execution_context() -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        assert isinstance(context, AssetExecutionContext)
        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]


def test_isinstance_op_execution_context_asset_execution_context() -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        assert type(context) is AssetExecutionContext
        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]


def test_op_gets_actual_op_execution_context() -> None:
    called = {"yup": False}

    @op
    def an_op(context: OpExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        assert type(context) is OpExecutionContext
        called["yup"] = True

    @job
    def a_job():
        an_op()

    assert a_job.execute_in_process().success
    assert called["yup"]


def test_run_id_in_asset_execution_context() -> None:
    called = {"yup": False}

    @asset
    def an_asset(context: AssetExecutionContext):
        # we make this work for backwards compat
        assert isinstance(context, OpExecutionContext)
        assert type(context) is AssetExecutionContext
        assert context.run_id
        called["yup"] = True

    assert materialize([an_asset]).success
    assert called["yup"]
