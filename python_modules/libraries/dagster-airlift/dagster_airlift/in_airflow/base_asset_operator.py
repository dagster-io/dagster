import logging
import os
import time
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

import requests
from airflow.models import BaseOperator
from requests import Response

from dagster_airlift.constants import DAG_ID_TAG_KEY, DAG_RUN_ID_TAG_KEY, TASK_ID_TAG_KEY
from dagster_airlift.in_airflow.dagster_run_utils import DagsterRunResult
from dagster_airlift.in_airflow.gql_queries import (
    ASSET_NODES_QUERY,
    RUNS_QUERY,
    TRIGGER_ASSETS_MUTATION,
    VERIFICATION_QUERY,
)
from dagster_airlift.in_airflow.partition_utils import (
    PARTITION_NAME_TAG,
    PartitioningInformation,
    translate_logical_date_to_partition_key,
)

logger = logging.getLogger(__name__)

# A job in dagster is uniquely defined by (location_name, repository_name, job_name).
DagsterJobIdentifier = tuple[str, str, str]

# Airflow context type. Instead of using a strongly typed `Context` from Airflow 2.x,
# it is defined as a generic mapping for compatibility with Airflow 1.x
Context = Mapping[str, Any]

IMPLICIT_ASSET_JOB_PREFIX = "__ASSET_JOB"

DEFAULT_DAGSTER_RUN_STATUS_POLL_INTERVAL = 1


class BaseDagsterAssetsOperator(BaseOperator, ABC):
    """Interface for an operator which materializes dagster assets.

    This operator needs to implement the following methods:

        - get_dagster_session: Returns a requests session that can be used to make requests to the Dagster API.
            This is where any additional authentication can be added.
        - get_dagster_url: Returns the URL for the Dagster instance.
        - filter_asset_nodes: Filters asset nodes (which are returned from Dagster's graphql API) to only include those
            that should be triggered by the current task.

    Optionally, these methods can be overridden as well:

        - get_partition_key: Determines the partition key to use to trigger the dagster run. This method will only be
            called if the underlying asset is partitioned.
    """

    def __init__(
        self,
        dagster_run_status_poll_interval: int = DEFAULT_DAGSTER_RUN_STATUS_POLL_INTERVAL,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.dagster_run_status_poll_interval = dagster_run_status_poll_interval

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

    def get_partition_key(
        self, context: Context, partitioning_info: PartitioningInformation
    ) -> str:
        """Overrideable method to determine the partition key to use to trigger the dagster run.

        This method will only be called if the underlying asset is partitioned.
        """
        if not partitioning_info:
            return None
        return translate_logical_date_to_partition_key(
            self.get_airflow_logical_date(context), partitioning_info
        )

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

    def get_dagster_run_obj(
        self, session: requests.Session, dagster_url: str, run_id: str
    ) -> Mapping[str, Any]:
        response = session.post(
            f"{dagster_url}/graphql",
            json={"query": RUNS_QUERY, "variables": {"runId": run_id}},
            # Timeout in seconds
            timeout=3,
        )
        return self.get_valid_graphql_response(response, "runOrError")

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

    def get_airflow_logical_date(self, context: Context) -> datetime:
        return self.get_attribute_from_airflow_context(context, "logical_date")

    def default_dagster_run_tags(self, context: Context) -> dict[str, str]:
        return {
            DAG_ID_TAG_KEY: self.get_airflow_dag_id(context),
            DAG_RUN_ID_TAG_KEY: self.get_airflow_dag_run_id(context),
            TASK_ID_TAG_KEY: self.get_airflow_task_id(context),
        }

    def launch_runs_for_task(self, context: Context, dag_id: str, task_id: str) -> None:
        """Launches runs for the given task in Dagster."""
        session = self._get_validated_session(context)
        dagster_url = self.get_dagster_url(context)

        asset_nodes_data = self.get_all_asset_nodes(session, dagster_url, context)
        logger.info(f"Got response {asset_nodes_data}")
        filtered_asset_nodes = [
            asset_node
            for asset_node in self.filter_asset_nodes(context, asset_nodes_data)
            if _is_asset_node_executable(asset_node)
        ]
        if not filtered_asset_nodes:
            raise Exception(f"No asset nodes found to trigger for task {dag_id}.{task_id}")
        if (
            not len(
                {_get_implicit_job_identifier(asset_node) for asset_node in filtered_asset_nodes}
            )
            == 1
        ):
            raise Exception(
                "Could not find an implicit asset job that can trigger all assets in this task. "
                "This may mean that you need to upgrade your Dagster version (1.8 or later), which allows all assets to be materialized in a single run, "
                "or that the assets are not in the same code location. "
                "`dagster-airlift` expects that all assets mapped to a given task exist within the same code location, so that they can be executed by the same run."
            )

        job_identifier = _get_implicit_job_identifier(next(iter(filtered_asset_nodes)))
        asset_key_paths = [asset_node["assetKey"]["path"] for asset_node in filtered_asset_nodes]
        logger.info(f"Triggering run for {job_identifier} with assets {asset_key_paths}")
        tags = self.default_dagster_run_tags(context)
        partitioning_info = PartitioningInformation.from_asset_node_graphql(filtered_asset_nodes)
        if partitioning_info:
            tags[PARTITION_NAME_TAG] = self.get_partition_key(context, partitioning_info)
        logger.info(f"Using tags {tags}")
        run_id = self.launch_dagster_run(
            context,
            session,
            dagster_url,
            build_dagster_run_execution_params(
                tags,
                job_identifier,
                asset_key_paths=asset_key_paths,
            ),
        )
        logger.info("Waiting for dagster run completion...")
        self.wait_for_run_and_retries_to_complete(
            session=session, dagster_url=dagster_url, run_id=run_id
        )
        logger.info("All runs completed successfully.")
        return None

    def wait_for_run_to_complete(
        self, session: requests.Session, dagster_url: str, run_id: str
    ) -> DagsterRunResult:
        while True:
            response = self.get_dagster_run_obj(session, dagster_url, run_id)
            status = response["status"]
            if status in ["SUCCESS", "FAILURE", "CANCELED"]:
                break
            time.sleep(self.dagster_run_status_poll_interval)
        tags = {tag["key"]: tag["value"] for tag in response["tags"]}
        return DagsterRunResult(status=response["status"], tags=tags)

    def wait_for_run_and_retries_to_complete(
        self, session: requests.Session, dagster_url: str, run_id: str
    ) -> None:
        run_id_to_check = run_id
        while True:
            result = self.wait_for_run_to_complete(
                session=session, dagster_url=dagster_url, run_id=run_id_to_check
            )
            if result.succeeded:
                break
            logger.info(f"Run {run_id_to_check} completed with status '{result.status}'.")
            if result.run_will_automatically_retry and result.retried_run_id:
                logger.info(
                    f"Run {run_id_to_check} retried in run {result.retried_run_id}. Waiting for completion..."
                )
                run_id_to_check = result.retried_run_id
                continue
            elif result.run_will_automatically_retry:
                logger.info(
                    f"Run {run_id_to_check} failed, but is configured to automatically retry. Waiting for retried run to be created..."
                )
                continue
            else:
                raise Exception(f"Run {run_id_to_check} failed, and is not expected to retry.")
        return None

    def execute(self, context: Context) -> Any:
        # https://github.com/apache/airflow/discussions/24463
        os.environ["NO_PROXY"] = "*"
        dag_id = os.environ["AIRFLOW_CTX_DAG_ID"]
        task_id = os.environ["AIRFLOW_CTX_TASK_ID"]
        return self.launch_runs_for_task(context, dag_id, task_id)


def _get_implicit_job_identifier(asset_node: Mapping[str, Any]) -> DagsterJobIdentifier:
    """Extracts the implicit job identifier from an asset node.

    In dagster 1.8 and later, there is a single implicit asset job constructed across all assets.
    Using this job to execute assets allows us to minimize the number of runs we need to launch,
    and ensures that assets are executed in topological order.
    """
    # In dagster 1.8 and later, there is a single implicit asset job constructed across all assets. Using this job to execute the asset is preferred, because
    # it minimizes the number of runs we need to launch, and ensures that assets are executed
    implicit_asset_job = next(
        iter(
            [job for job in asset_node["jobs"] if job["name"].startswith(IMPLICIT_ASSET_JOB_PREFIX)]
        ),
        None,
    )
    job_to_use = implicit_asset_job or asset_node["jobs"][0]
    location_name = job_to_use["repository"]["location"]["name"]
    repository_name = job_to_use["repository"]["name"]
    job_name = job_to_use["name"]
    return (location_name, repository_name, job_name)


def build_dagster_run_execution_params(
    tags: Mapping[str, Any],
    job_identifier: DagsterJobIdentifier,
    asset_key_paths: Sequence[Sequence[str]],
) -> dict[str, Any]:
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


def _build_runs_filter_param(tags: Mapping[str, Any]) -> Mapping[str, Any]:
    return {"tags": [{"key": key, "value": value} for key, value in tags.items()]}
