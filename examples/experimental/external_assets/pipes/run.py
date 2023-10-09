from dagster_pipes import init_dagster_pipes

context = init_dagster_pipes()
context.log.info("hello world")
context.report_asset_materialization(metadata={"i_am": "metadata"})
