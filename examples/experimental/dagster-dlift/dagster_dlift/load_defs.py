from typing import Dict

from dagster import (
    AssetKey,
    AssetMaterialization,
    AssetSpec,
    Definitions,
    SensorDefinition,
    SensorResult,
    sensor,
)
from dagster._core.storage.tags import KIND_PREFIX

from dagster_dlift.dbt_gql_queries import GET_DBT_MODELS_QUERY, GET_DBT_RUNS_QUERY
from dagster_dlift.instance import DbtCloudInstance


def load_defs_from_dbt_cloud_instance(
    instance: DbtCloudInstance,
) -> Definitions:
    all_model_infos = {}
    unique_id_deps = {}
    for environment_id in instance.list_environment_ids():
        print(f"SCANNING MODEL INFOS FOR ENVIRONMENT {environment_id}")
        response = instance.ensure_valid_response(
            instance.query_discovery_api(
                GET_DBT_MODELS_QUERY,
                {"environmentId": environment_id, "types": ["Model"], "first": 100},
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
        for model in all_model_infos[environment_id]:
            unique_id_deps[model["unique_id"]] = [
                ancestor["uniqueId"] for ancestor in model["ancestors"]
            ]
    sensor_def = dbt_cloud_runs_sensor(
        instance,
        {
            env_id: {
                model_info["unique_id"]: AssetKey([model_info["unique_id"]])
                for model_info in model_infos
            }
            for env_id, model_infos in all_model_infos.items()
        },
    )
    return Definitions(
        assets=[
            AssetSpec(
                AssetKey([model_info["unique_id"]]),
                tags={f"{KIND_PREFIX}dbt": ""},
                deps=[AssetKey([dep]) for dep in unique_id_deps[model_info["unique_id"]]],
            )
            for env_id, model_infos in all_model_infos.items()
            for model_info in model_infos
        ],
        sensors=[sensor_def],
    )


def dbt_cloud_runs_sensor(
    instance: DbtCloudInstance, unique_id_to_assets: Dict[str, Dict[str, AssetKey]]
) -> SensorDefinition:
    @sensor(name="dbt_cloud_instance_sensor", asset_selection="*")
    def dbt_cloud_runs_sensor_fn(context) -> SensorResult:
        asset_mats = []
        for environment_id, unique_id_map in unique_id_to_assets.items():
            for unique_id, asset_key in unique_id_map.items():
                response = instance.ensure_valid_response(
                    instance.query_discovery_api(
                        GET_DBT_RUNS_QUERY,
                        {"environmentId": environment_id, "uniqueId": unique_id},
                    )
                )
                print(f"RESPONSE JSON: {response.json()}")
                runs = response.json()["data"]["environment"]["applied"]["modelHistoricalRuns"]
                for run in runs:
                    print(f"FOUND RUN: {run}")
                    asset_mats.append(
                        AssetMaterialization(
                            asset_key=asset_key,
                            # Not sure why run results is a list here, but we'll just take the first one
                            metadata={
                                "dbt_cloud_job_id": run["jobId"],
                                "dbt_cloud_run_id": run["runId"],
                                "dbt_cloud_run_name": run["name"],
                                "dbt_cloud_run_status": next(iter(run["runResults"]))["status"],
                            },
                        )
                    )
        return SensorResult(asset_events=asset_mats)

    return dbt_cloud_runs_sensor_fn
