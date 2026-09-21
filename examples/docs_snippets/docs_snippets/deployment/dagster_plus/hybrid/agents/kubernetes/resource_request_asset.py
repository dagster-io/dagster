from dagster_k8s import k8s_job_executor

import dagster as dg


@dg.asset(
    op_tags={
        "dagster-k8s/config": {
            "container_config": {
                "resources": {
                    "limits": {
                        "cpu": "500m",
                        "memory": "2560Mi",
                        "nvidia.com/gpu": "1",
                    },
                },
            },
        }
    }
)
def train_model(): ...


training_job = dg.define_asset_job(
    name="training_job",
    selection=dg.AssetSelection.assets(train_model),
    executor_def=k8s_job_executor,
)
