from typing import Any, Dict, List
from dagster_airlift.in_airflow.dagster_operator import launch_runs_for_task
from dagster_airlift.in_airflow.gql_queries import ASSET_NODES_QUERY, TRIGGER_ASSETS_MUTATION
import responses
from dagster import AssetKey

def build_asset_nodes_response_for_dag_structure(dag_structure: Dict[str, Dict[str, List[str]]]) -> None:
    """Given a dag_structure, build a response_dict that would be returned by the graphql server and set it for the payload."""
    response_dict = {"data": {"assetNodes": []}}
    for dag_id, task_structure in dag_structure.items():
        for task_id, asset_keys in task_structure.items():
            for asset_key in asset_keys:
                response_dict["data"]["assetNodes"].append(
                    {
                        "opName": f"{asset_key}_op",
                        "tags": [{"key": "airlift/dag_id", "value": dag_id}, {"key": "airlift/task_id", "value": task_id}],
                        "jobs": [
                            {
                                "repository": {
                                    "location": {"name": "location_name"},
                                    "name": "repo_name",
                                },
                                "name": "job_name",
                            }
                        ],
                        "assetKey": {"path": AssetKey.from_user_string(asset_key).path},
                    }
                )

    responses.add(responses.POST, "http://dagster_url/graphql", json=response_dict, match=[responses.json_params_matcher({"query": ASSET_NODES_QUERY})])

def build_trigger_assets_response() -> None:
    """Build a response_dict that would be returned by the graphql server for the mutation that triggers assets."""
    response_dict = {"data": {"launchPipelineExecution": {"run": {"id": "run_id"}}}}
    responses.add(responses.POST, "http://dagster_url/graphql", json=response_dict, match=[responses.json_params_matcher({"query": TRIGGER_ASSETS_MUTATION})])

def build_runs_query_response() -> None:
    """Build a response_dict that would be returned by the graphql server for the query that checks the status of runs."""
    response_dict = {"data": {"run": {"status": "SUCCESS"}}}
    responses.add(responses.POST, "http://dagster_url/graphql", json=response_dict)


@responses.activate
def test_launch_runs_for_task() -> None:
    """Test that launch_runs_for_task triggers the correct runs for the given task."""
    dag_structure = {
        "dag": {
            "task": ["asset1", "asset2"],
        }
    }
    build_asset_nodes_response_for_dag_structure(dag_structure)
    _asset_nodes_count = [0]
    build_trigger_assets_response()
    _trigger_assets_count = [0]
    build_runs_query_response()
    _runs_query_count = [0]
    launch_runs_for_task("dag_id", "task_id", "dagster_url")