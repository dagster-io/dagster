import time
from dagster.core.asset_defs import asset, build_assets_job


@asset
def my_asset(context):
    while True:
        context.log.info("im sleeping")
        time.sleep(1)


hanging_asset_job = build_assets_job(
    "story_recommender_prod",
    assets=[my_asset],
)
