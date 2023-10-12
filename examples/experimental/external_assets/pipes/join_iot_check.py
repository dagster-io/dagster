from dagster_pipes import open_dagster_pipes

with open_dagster_pipes() as pipes:
    pipes.log.info("checking iot telem data....")
    pipes.report_asset_check(
        asset_key="telem_post_processing", check_name="telem_post_processing_check", passed=True
    )
