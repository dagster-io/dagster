from dagster import asset


@asset
def upstream_asset() -> int:
    return 1


def old_config() -> None:
    # begin_old_config

    from dagster import AssetExecutionContext, Definitions, asset

    @asset(config_schema={"conn_string": str, "port": int})
    def an_asset(context: AssetExecutionContext, upstream_asset):
        assert context.op_execution_context.op_config["conn_string"]
        assert context.op_execution_context.op_config["port"]

    defs = Definitions(assets=[an_asset, upstream_asset])

    job_def = defs.get_implicit_global_asset_job_def()

    result = job_def.execute_in_process(
        run_config={"ops": {"an_asset": {"config": {"conn_string": "foo", "port": 1}}}}
    )

    # end_old_config

    assert result.success


def new_config_schema() -> None:
    # begin_new_config_schema
    from dagster import Config, Definitions, asset

    class AnAssetConfig(Config):
        conn_string: str
        port: int

    @asset
    def an_asset(upstream_asset, config: AnAssetConfig):
        assert config.conn_string
        assert config.port

    defs = Definitions(assets=[an_asset, upstream_asset])

    job_def = defs.get_implicit_global_asset_job_def()

    # code to launch/execute jobs is unchanged
    result = job_def.execute_in_process(
        run_config={"ops": {"an_asset": {"config": {"conn_string": "foo", "port": 1}}}}
    )

    # end_new_config_schema

    assert result.success


def new_config_schema_and_typed_run_config() -> None:
    from dagster import Config, Definitions, RunConfig, asset

    class AnAssetConfig(Config):
        conn_string: str
        port: int

    @asset
    def an_asset(upstream_asset, config: AnAssetConfig):
        assert config.conn_string
        assert config.port

    defs = Definitions(assets=[an_asset, upstream_asset])

    job_def = defs.get_implicit_global_asset_job_def()

    # begin_new_config_schema_and_typed_run_config

    result = job_def.execute_in_process(
        run_config=RunConfig(ops={"an_asset": AnAssetConfig(conn_string="foo", port=1)})
    )

    # end_new_config_schema_and_typed_run_config

    assert result.success
