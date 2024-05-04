from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    pipes.log.info("do stuff")

    pipes.report_asset_materialization(
        asset_key="some_group/asset_three", metadata={"some": "metadata"}
    )
    pipes.report_asset_materialization(
        asset_key="some_group/asset_four", metadata={"some": "other_metadata"}
    )
