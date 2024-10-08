import logging
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

import requests
from airflow.models.operator import BaseOperator
from airflow.utils.context import Context
from requests import Response

from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY, TASK_ID_TAG_KEY

from .gql_queries import ASSET_NODES_QUERY, RUNS_QUERY, TRIGGER_ASSETS_MUTATION, VERIFICATION_QUERY

logger = logging.getLogger(__name__)

# A job in dagster is uniquely defined by (location_name, repository_name, job_name).
DagsterJobIdentifier = Tuple[str, str, str]


class BaseDagsterAssetsOperator(BaseOperator, ABC):
    """Interface for an operator which materializes dagster assets."""

    @abstractmethod
    def get_dagster_session(self, context: Context) -> requests.Session:
        """Returns a requests session that can be used to make requests to the Dagster API."""

    def _get_validated_session(self, context: Context) -> requests.Session:
        session = self.get_dagster_session(context)
        dagster_url = self.get_dagster_url(context)
        response = session.post(
            # Timeout in seconds
            f"{dagster_url}/graphql",
            json={"query": VERIFICATION_QUERY},
            timeout=3,
        )
        if response.status_code != 200:
            raise Exception(
                f"Failed to connect to Dagster at {dagster_url}. Response: {response.text}"
            )
        return session

    @abstractmethod
    def get_dagster_url(self, context: Context) -> str:
        """Returns the URL for the Dagster instance."""

    @abstractmethod
    def filter_asset_nodes(
        self, context: Context, asset_nodes: Sequence[Mapping[str, Any]]
    ) -> Iterable[Mapping[str, Any]]:
        """Filters the asset nodes to only include those that should be triggered by the current task."""

    def get_valid_graphql_response(self, response: Response, key: str) -> Any:
        response_json = response.json()
        if not response_json.get("data"):
            raise Exception(f"Error in GraphQL request. No data key: {response_json}")

        if key not in response_json["data"]:
            raise Exception(f"Error in GraphQL request. No {key} key: {response_json}")

        return response_json["data"][key]

    def get_all_asset_nodes(
        self, session: requests.Session, dagster_url: str, context: Context
    ) -> Sequence[Mapping[str, Any]]:
        # create graphql client
        response = session.post(
            # Timeout in seconds
            f"{dagster_url}/graphql",
            json={"query": ASSET_NODES_QUERY},
            timeout=3,
        )
        return self.get_valid_graphql_response(response, "assetNodes")

    def launch_dagster_run(
        self,
        context: Context,
        session: requests.Session,
        dagster_url: str,
        execution_params: Mapping[str, Any],
    ) -> str:
        response = session.post(
            f"{dagster_url}/graphql",
            json={
                "query": TRIGGER_ASSETS_MUTATION,
                "variables": {"executionParams": execution_params},
            },
            # Timeout in seconds
            timeout=10,
        )
        launch_data = self.get_valid_graphql_response(response, "launchPipelineExecution")
        return launch_data["run"]["id"]

    def get_dagster_run_status(
        self, session: requests.Session, dagster_url: str, run_id: str
    ) -> str:
        response = session.post(
            f"{dagster_url}/graphql",
            json={"query": RUNS_QUERY, "variables": {"runId": run_id}},
            # Timeout in seconds
            timeout=3,
        )
        return self.get_valid_graphql_response(response, "runOrError")["status"]

    def get_attribute_from_airflow_context(self, context: Context, attribute: str) -> Any:
        if attribute not in context or context[attribute] is None:
            raise Exception(f"Attribute {attribute} not found in context.")
        return context[attribute]

    def get_airflow_dag_run_id(self, context: Context) -> str:
        return self.get_attribute_from_airflow_context(context, "dag_run").run_id

    def get_airflow_dag_id(self, context: Context) -> str:
        return self.get_attribute_from_airflow_context(context, "dag_run").dag_id

    def get_airflow_task_id(self, context: Context) -> str:
        return self.get_attribute_from_airflow_context(context, "task").task_id

    def default_dagster_run_tags(self, context: Context) -> Dict[str, str]:
        return {
            DAG_ID_TAG_KEY: self.get_airflow_dag_id(context),
            DAG_RUN_ID_TAG_KEY: self.get_airflow_dag_run_id(context),
            TASK_ID_TAG_KEY: self.get_airflow_task_id(context),
        }

    def launch_runs_for_task(self, context: Context, dag_id: str, task_id: str) -> None:
        """Launches runs for the given task in Dagster."""
        session = self._get_validated_session(context)
        dagster_url = self.get_dagster_url(context)

        assets_to_trigger_per_job: Dict[DagsterJobIdentifier, List[Sequence[str]]] = defaultdict(
            list
        )
        asset_nodes_data = self.get_all_asset_nodes(session, dagster_url, context)
        logger.info(f"Got response {asset_nodes_data}")
        filtered_asset_nodes = [
            asset_node
            for asset_node in self.filter_asset_nodes(context, asset_nodes_data)
            if _is_asset_node_executable(asset_node)
        ]
        if not filtered_asset_nodes:
            raise Exception(f"No asset nodes found to trigger for task {dag_id}.{task_id}")
        for asset_node in filtered_asset_nodes:
            assets_to_trigger_per_job[_build_dagster_job_identifier(asset_node)].append(
                asset_node["assetKey"]["path"]
            )
        logger.debug(f"Found {len(assets_to_trigger_per_job)} jobs to trigger")

        triggered_runs = []
        for job_identifier, asset_key_paths in assets_to_trigger_per_job.items():
            logger.debug(f"Triggering run for {job_identifier} with assets {asset_key_paths}")
            run_id = self.launch_dagster_run(
                context,
                session,
                dagster_url,
                _build_dagster_run_execution_params(
                    self.default_dagster_run_tags(context),
                    job_identifier,
                    asset_key_paths,
                ),
            )
            triggered_runs.append(run_id)
        completed_runs = {}  # key is run_id, value is status
        while len(completed_runs) < len(triggered_runs):
            for run_id in triggered_runs:
                if run_id in completed_runs:
                    continue
                run_status = self.get_dagster_run_status(session, dagster_url, run_id)
                if run_status in ["SUCCESS", "FAILURE", "CANCELED"]:
                    logger.debug(f"Run {run_id} completed with status {run_status}")
                    completed_runs[run_id] = run_status
        non_successful_runs = [
            run_id for run_id, status in completed_runs.items() if status != "SUCCESS"
        ]
        if non_successful_runs:
            raise Exception(f"Runs {non_successful_runs} did not complete successfully.")
        logger.debug("All runs completed successfully.")
        return None

    def execute(self, context: Context) -> Any:
        # https://github.com/apache/airflow/discussions/24463
        os.environ["NO_PROXY"] = "*"
        dag_id = os.environ["AIRFLOW_CTX_DAG_ID"]
        task_id = os.environ["AIRFLOW_CTX_TASK_ID"]
        return self.launch_runs_for_task(context, dag_id, task_id)


def _build_dagster_job_identifier(asset_node: Mapping[str, Any]) -> DagsterJobIdentifier:
    location_name = asset_node["jobs"][0]["repository"]["location"]["name"]
    repository_name = asset_node["jobs"][0]["repository"]["name"]
    job_name = asset_node["jobs"][0]["name"]
    return (location_name, repository_name, job_name)


def _build_dagster_run_execution_params(
    tags: Mapping[str, Any],
    job_identifier: DagsterJobIdentifier,
    asset_key_paths: Sequence[Sequence[str]],
) -> Dict[str, Any]:
    location_name, repository_name, job_name = job_identifier
    return {
        "mode": "default",
        "executionMetadata": {
            "tags": [{"key": key, "value": value} for key, value in tags.items()]
        },
        "runConfigData": "{}",
        "selector": {
            "repositoryLocationName": location_name,
            "repositoryName": repository_name,
            "pipelineName": job_name,
            "assetSelection": [{"path": asset_key} for asset_key in asset_key_paths],
            "assetCheckSelection": [],
        },
    }


def _is_asset_node_executable(asset_node: Mapping[str, Any]) -> bool:
    return bool(asset_node["jobs"])
