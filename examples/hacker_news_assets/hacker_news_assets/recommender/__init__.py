from hacker_news_assets.core import core_assets_local, core_assets_prod, core_assets_staging
from hacker_news_assets.sensors.hn_tables_updated_sensor import make_hn_tables_updated_sensor

from dagster import AssetGroup

from . import assets

recommender_assets = load_assets_from_package({assets}, prefix="recommender")

recommender_job_spec = JobSpec(
    selection="recommender>comment_stories*", name="story_recommender_job"
)  # probably can do better here
recommender_assets_sensor = make_hn_tables_updated_sensor(job_name=recommender_job_spec.name)
