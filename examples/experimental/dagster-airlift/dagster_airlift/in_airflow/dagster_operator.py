import os

import requests
from airflow import DAG
from airflow.operators.python import PythonOperator

from .gql_queries import ASSET_NODES_QUERY, RUNS_QUERY, TRIGGER_ASSETS_MUTATION


def compute_fn() -> None:
    # https://github.com/apache/airflow/discussions/24463
    os.environ["NO_PROXY"] = "*"
    dag_id = os.environ["AIRFLOW_CTX_DAG_ID"]
    task_id = os.environ["AIRFLOW_CTX_TASK_ID"]
    expected_op_name = f"{dag_id}__{task_id}"
    assets_to_trigger = {}  # key is (repo_location, repo_name, job_name), value is list of asset keys
    # create graphql client
    dagster_url = os.environ["DAGSTER_URL"]
    response = requests.post(f"{dagster_url}/graphql", json={"query": ASSET_NODES_QUERY}, timeout=3)
    for asset_node in response.json()["data"]["assetNodes"]:
        if asset_node["opName"] == expected_op_name:
            repo_location = asset_node["jobs"][0]["repository"]["location"]["name"]
            repo_name = asset_node["jobs"][0]["repository"]["name"]
            job_name = asset_node["jobs"][0]["name"]
            if (repo_location, repo_name, job_name) not in assets_to_trigger:
                assets_to_trigger[(repo_location, repo_name, job_name)] = []
            assets_to_trigger[(repo_location, repo_name, job_name)].append(
                asset_node["assetKey"]["path"]
            )
    print(f"Found assets to trigger: {assets_to_trigger}")  # noqa: T201
    triggered_runs = []
    for (repo_location, repo_name, job_name), asset_keys in assets_to_trigger.items():
        execution_params = {
            "mode": "default",
            "executionMetadata": {"tags": []},
            "runConfigData": "{}",
            "selector": {
                "repositoryLocationName": repo_location,
                "repositoryName": repo_name,
                "pipelineName": job_name,
                "assetSelection": [{"path": asset_key} for asset_key in asset_keys],
                "assetCheckSelection": [],
            },
        }
        print(f"Triggering run for {repo_location}/{repo_name}/{job_name} with assets {asset_keys}")  # noqa: T201
        response = requests.post(
            f"{dagster_url}/graphql",
            json={
                "query": TRIGGER_ASSETS_MUTATION,
                "variables": {"executionParams": execution_params},
            },
            timeout=3,
        )
        run_id = response.json()["data"]["launchPipelineExecution"]["run"]["id"]
        print(f"Launched run {run_id}...")  # noqa: T201
        triggered_runs.append(run_id)
    completed_runs = {}  # key is run_id, value is status
    while len(completed_runs) < len(triggered_runs):
        for run_id in triggered_runs:
            if run_id in completed_runs:
                continue
            response = requests.post(
                f"{dagster_url}/graphql",
                json={"query": RUNS_QUERY, "variables": {"runId": run_id}},
                timeout=3,
            )
            run_status = response.json()["data"]["runOrError"]["status"]
            if run_status in ["SUCCESS", "FAILURE", "CANCELED"]:
                print(f"Run {run_id} completed with status {run_status}")  # noqa: T201
                completed_runs[run_id] = run_status
    non_successful_runs = [
        run_id for run_id, status in completed_runs.items() if status != "SUCCESS"
    ]
    if non_successful_runs:
        raise Exception(f"Runs {non_successful_runs} did not complete successfully.")
    print("All runs completed successfully.")  # noqa: T201
    return None


def build_dagster_task(task_id: str, dag: DAG, **kwargs):
    return PythonOperator(task_id=task_id, dag=dag, python_callable=compute_fn, **kwargs)
