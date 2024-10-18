from typing import Dict

from dagster import (
    AssetKey,
    AssetMaterialization,
    Definitions,
    SensorDefinition,
    SensorResult,
    asset,
    asset_check,
    sensor,
    AssetSpec
)
from dagster._core.definitions.asset_check_result import AssetCheckResult
from dagster._core.storage.tags import KIND_PREFIX

from dagster_dlift.dbt_gql_queries import GET_DBT_MODELS_QUERY, GET_DBT_RUNS_QUERY, GET_DBT_SOURCES_QUERY, GET_DBT_TESTS_QUERY
from dagster_dlift.instance import DbtCloudInstance


def load_defs_from_dbt_cloud_instance(
    instance: DbtCloudInstance,
) -> Definitions:
    all_model_infos = {}
    unique_id_deps = {}
    triggerable_job_per_unique_id = {}
    all_source_infos = {}
    all_test_infos = {}
    for environment_id in instance.list_environment_ids():
        response = instance.ensure_valid_response(
            instance.query_discovery_api(
                GET_DBT_MODELS_QUERY,
                {"environmentId": environment_id, "first": 100},
            )
        )
        all_model_infos[environment_id] = [
            {
                "unique_id": model["node"]["uniqueId"],
                "parents": model["node"]["parents"],
                "jobDefinitionId": model["node"]["jobDefinitionId"],
            }
            for model in response.json()["data"]["environment"]["definition"]["models"]["edges"]
        ]
        for model in all_model_infos[environment_id]:
            unique_id_deps[model["unique_id"]] = [
                ancestor["uniqueId"] for ancestor in model["parents"]
            ]
            if "jobDefinitionId" in model:
                triggerable_job_per_unique_id[model["unique_id"]] = model["jobDefinitionId"]
            else:
                raise Exception(f"Model {model['unique_id']} is not triggerable")
        
        response = instance.ensure_valid_response(
            instance.query_discovery_api(
                GET_DBT_SOURCES_QUERY,
                {"environmentId": environment_id, "first": 100},
            )
        )
        all_source_infos[environment_id] = [
            {
                "unique_id": source["node"]["uniqueId"],
                "source_name": source["node"]["sourceName"],
                "source_description": source["node"]["sourceDescription"],
            }
            for source in response.json()["data"]["environment"]["definition"]["sources"]["edges"]
        ]
        response = instance.ensure_valid_response(
            instance.query_discovery_api(
                GET_DBT_TESTS_QUERY,
                {"environmentId": environment_id, "first": 100},
            )
        )
        all_test_infos[environment_id] = [
            {
                "name": test["node"]["name"],
                "testType": test["node"]["testType"],
                "jobDefinitionId": test["node"]["jobDefinitionId"],
                "parent_unique_id": [parent["uniqueId"] for parent in test["node"]["parents"] if parent["resourceType"] == "model"],
            }
            for test in response.json()["data"]["environment"]["definition"]["tests"]["edges"]
        ]
        for test in all_test_infos[environment_id]:
            if "jobDefinitionId" in test:
                triggerable_job_per_unique_id[test["name"]] = test["jobDefinitionId"]
            else:
                raise Exception(f"Test {test['name']} is not triggerable")

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
    assets = []
    checks = []
    for env_id, model_infos in all_model_infos.items():
        for model_info in model_infos:

            @asset(
                key=AssetKey([model_info["unique_id"].replace(".", "_")]),
                tags={f"{KIND_PREFIX}dbt": ""},
                deps=[
                    AssetKey([dep.replace(".", "_")])
                    for dep in unique_id_deps[model_info["unique_id"]]
                ],
            )
            def _the_asset(context) -> None:
                print(f"TRIGGERING JOB FOR {model_info['unique_id']}")
                run_id = instance.trigger_job(
                    job_id=triggerable_job_per_unique_id[model_info["unique_id"]],
                    model_unique_id=model_info["unique_id"],
                )
                print(f"TRIGGERED JOB {run_id}")

            assets.append(_the_asset)
    
    for env_id, source_infos in all_source_infos.items():
        for source_info in source_infos:
            assets.append(AssetSpec(AssetKey([source_info["unique_id"].replace(".", "_")]), tags={f"{KIND_PREFIX}dbt": "", f"{KIND_PREFIX}source": ""}))
    
    for env_id, test_infos in all_test_infos.items():
        for test_info in test_infos:
            # Not sure if there can actually be multiple here? Seems like it's one model and a bunch of macros in jaffle shop at least
            upstream_models = [AssetKey([parent.replace(".", "_")]) for parent in test_info["parent_unique_id"]]
            @asset_check(
                asset=upstream_models[0],
                name=test_info["name"],
                additional_deps=upstream_models[1:],
                description=f"DBT Test {test_info['name']} failed",
            )
            def _the_asset_check(context) -> AssetCheckResult:
                print(f"TRIGGERING TEST FOR {test_info['name']}")
                run_id = instance.trigger_job_test(
                    job_id=triggerable_job_per_unique_id[test_info["name"]],
                    test_unique_id=test_info["name"],
                )
                print(f"TRIGGERED TEST {run_id}")
                return AssetCheckResult(passed=True)
            checks.append(_the_asset_check)


    
    return Definitions(
        assets=assets,
        sensors=[sensor_def],
        asset_checks=checks,
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
