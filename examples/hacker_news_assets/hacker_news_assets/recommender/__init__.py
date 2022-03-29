from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import assets_from_package_module, build_assets_job, namespaced

from . import assets

recommender_assets = namespaced("recommender", assets_from_package_module(assets))

recommender_assets_sensor = make_hn_tables_updated_sensor(
    build_assets_job(
        name="story_recommender_job",
        assets=recommender_assets,
    )
)

recommender_definitions = recommender_assets + [recommender_assets_sensor]
