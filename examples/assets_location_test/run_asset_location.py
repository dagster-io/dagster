from dagster import execute_job, DagsterInstance
from asset_location import custom_pipeline

if __name__ == "__main__":
    instance = DagsterInstance.get()
    result = execute_job(custom_pipeline, instance=instance)
    assets_def = result.job_def.get_solid("asset_us_west1").definition
    assets_def.render_asset_graph()