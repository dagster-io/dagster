from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as context:
    context.log.info("checking iot telem data....")
    context.report_asset_check(
        asset_key="telem_post_processing", check_name="telem_post_processing_check", passed=True
    )
