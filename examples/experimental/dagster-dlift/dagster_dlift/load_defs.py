from dagster import AssetKey, AssetSpec, Definitions
from dagster._core.storage.tags import KIND_PREFIX

from dagster_dlift.dbt_gql_queries import GET_DBT_MODELS_QUERY
from dagster_dlift.instance import DbtCloudInstance


def load_defs_from_dbt_cloud_instance(
    instance: DbtCloudInstance,
) -> Definitions:
    all_model_infos = {}
    for environment_id in instance.list_environment_ids():
        print(f"SCANNING MODEL INFOS FOR ENVIRONMENT {environment_id}")
        response = instance.ensure_valid_response(
            instance.query_discovery_api(
                GET_DBT_MODELS_QUERY,
                {"environmentId": environment_id, "types": ["Model"], "first": 1},
            )
        )
        print(f"RESPONSE STATUS CODE: {response.status_code}")
        print(f"RESPONSE JSON: {response.json()}")
        all_model_infos[environment_id] = [
            {
                "unique_id": model["node"]["uniqueId"],
                "ancestors": model["node"]["ancestors"],
            }
            for model in response.json()["data"]["environment"]["definition"]["models"]["edges"]
        ]
    return Definitions(
        assets=[
            AssetSpec(AssetKey([model_info["unique_id"]]), tags={f"{KIND_PREFIX}dbt": ""})
            for env_id, model_infos in all_model_infos.items()
            for model_info in model_infos
        ],
    )
