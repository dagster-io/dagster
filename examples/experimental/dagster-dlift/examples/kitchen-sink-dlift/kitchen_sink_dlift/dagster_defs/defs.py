from dagster_dlift.load_defs import load_defs_from_dbt_cloud_instance

from kitchen_sink_dlift.dagster_defs.cloud_instance import get_dbt_cloud_instance

defs = load_defs_from_dbt_cloud_instance(get_dbt_cloud_instance("test"))
