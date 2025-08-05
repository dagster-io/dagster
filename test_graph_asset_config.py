from dagster import AssetExecutionContext, AssetIn, Config, Definitions, asset, define_asset_job, graph_asset


class UpstreamAssetConfig(Config):
    start_date: str = "2020-07-07"


# This asset configuration works as expected - the default value is used in the asset materialization and it shows the Dagster UI Launchpad  # noqa
@asset
def upstream_asset1(context: AssetExecutionContext, config: UpstreamAssetConfig) -> str:
    
    context.log.info(f"Upstream asset1 config: {config}")

    return config.start_date


@asset
def upstream_asset2(context: AssetExecutionContext, config: UpstreamAssetConfig) -> str:
    context.log.info(f"Upstream asset2 config: {config}")

    return config.start_date


# This asset configuration does not work as expected
@graph_asset(
    config={
        "upstream_asset2": {
            "config": {"start_date": "2020-06-06"}
        }
            # bug: this config does not show in the Dagster UI Launchpad (but it's used in the asset materialization!)  # noqa
    }
)
def upstream_graph_asset2():
    return upstream_asset2()


class DownstreamAssetConfig(Config):
    end_date: str = "2020-05-05"


@asset(ins={"upstream_asset1": AssetIn(), "upstream_graph_asset2": AssetIn()})
def downstream_asset(
    context: AssetExecutionContext, config: DownstreamAssetConfig, upstream_asset1: str, upstream_graph_asset2: str
) -> str:
    context.log.info(f"Upstream asset1: {upstream_asset1}")
    context.log.info(f"Upstream upstream_graph_asset2: {upstream_graph_asset2}")
    context.log.info(f"Downstream asset config: {config}")

    return config.end_date


jobs = [
    define_asset_job(name="materialize_assets", selection=[upstream_asset1, upstream_graph_asset2, downstream_asset])
]
defs = Definitions(assets=[upstream_asset1, upstream_graph_asset2, downstream_asset], jobs=jobs)
