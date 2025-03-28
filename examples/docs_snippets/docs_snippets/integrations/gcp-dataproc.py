from dagster_gcp import DataprocResource

import dagster as dg

dataproc_resource = DataprocResource(
    project_id="your-gcp-project-id",
    region="your-gcp-region",
    cluster_name="your-cluster-name",
    cluster_config_yaml_path="path/to/your/cluster/config.yaml",
)


@dg.asset
def my_dataproc_asset(dataproc: DataprocResource):
    client = dataproc.get_client()
    job_details = {
        "job": {
            "placement": {"clusterName": dataproc.cluster_name},
        }
    }
    client.submit_job(job_details)


defs = dg.Definitions(
    assets=[my_dataproc_asset], resources={"dataproc": dataproc_resource}
)
