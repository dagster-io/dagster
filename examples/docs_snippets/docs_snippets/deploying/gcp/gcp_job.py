from dagster_gcp.gcs.io_manager import gcs_pickle_io_manager
from dagster_gcp.gcs.resources import gcs_resource

from dagster import job


@job(
    resource_defs={
        "gcs": gcs_resource,
        "io_manager": gcs_pickle_io_manager,
    },
    config={
        "resources": {
            "io_manager": {
                "config": {
                    "gcs_bucket": "my-cool-bucket",
                    "gcs_prefix": "good/prefix-for-files-",
                }
            }
        }
    },
)
def gcs_job():
    ...
