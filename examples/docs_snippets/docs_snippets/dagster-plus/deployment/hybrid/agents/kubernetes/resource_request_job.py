import dagster as dg


@dg.asset
def prepare_model(): ...


@dg.asset(deps=[prepare_model])
def train_model(): ...


training_job = dg.define_asset_job(
    name="prepare_and_train_model_job",
    selection=dg.AssetSelection.assets(train_model).upstream(),
    tags={
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
    },
)
