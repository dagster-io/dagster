import inspect
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Set, Tuple, Type

import requests
from airflow.models.operator import BaseOperator
from airflow.utils.context import Context

from dagster_airlift.constants import DAG_ID_METADATA_KEY, TASK_ID_METADATA_KEY

from .gql_queries import ASSET_NODES_QUERY, RUNS_QUERY, TRIGGER_ASSETS_MUTATION, VERIFICATION_QUERY

logger = logging.getLogger(__name__)


class BaseProxyToDagsterOperator(BaseOperator, ABC):
    """Interface for a DagsterOperator.

    This interface is used to create a custom operator that will be used to replace the original airflow operator when a task is marked as migrated.
    """

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

    def launch_runs_for_task(self, context: Context, dag_id: str, task_id: str) -> None:
        """Launches runs for the given task in Dagster."""
        expected_op_name = f"{dag_id}__{task_id}"
        session = self._get_validated_session(context)

        dagster_url = self.get_dagster_url(context)
        assets_to_trigger = {}  # key is (repo_location, repo_name, job_name), value is list of asset keys
        # create graphql client
        response = session.post(
            # Timeout in seconds
            f"{dagster_url}/graphql",
            json={"query": ASSET_NODES_QUERY},
            timeout=3,
        )
        for asset_node in response.json()["data"]["assetNodes"]:
            text_metadata_entries = {
                entry["label"]: entry["text"]
                for entry in asset_node["metadataEntries"]
                if entry["__typename"] == "TextMetadataEntry"
            }
            # match assets based on conventional dag_id__task_id naming or based on explicit tags
            if asset_node["opName"] == expected_op_name or (
                text_metadata_entries.get(DAG_ID_METADATA_KEY) == dag_id
                and text_metadata_entries.get(TASK_ID_METADATA_KEY) == task_id
            ):
                repo_location = asset_node["jobs"][0]["repository"]["location"]["name"]
                repo_name = asset_node["jobs"][0]["repository"]["name"]
                job_name = asset_node["jobs"][0]["name"]
                if (repo_location, repo_name, job_name) not in assets_to_trigger:
                    assets_to_trigger[(repo_location, repo_name, job_name)] = []
                assets_to_trigger[(repo_location, repo_name, job_name)].append(
                    asset_node["assetKey"]["path"]
                )
        logger.debug(f"Found assets to trigger: {assets_to_trigger}")
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
            logger.debug(
                f"Triggering run for {repo_location}/{repo_name}/{job_name} with assets {asset_keys}"
            )
            response = session.post(
                f"{dagster_url}/graphql",
                json={
                    "query": TRIGGER_ASSETS_MUTATION,
                    "variables": {"executionParams": execution_params},
                },
                # Timeout in seconds
                timeout=10,
            )
            run_id = response.json()["data"]["launchPipelineExecution"]["run"]["id"]
            logger.debug(f"Launched run {run_id}...")
            triggered_runs.append(run_id)
        completed_runs = {}  # key is run_id, value is status
        while len(completed_runs) < len(triggered_runs):
            for run_id in triggered_runs:
                if run_id in completed_runs:
                    continue
                response = session.post(
                    f"{dagster_url}/graphql",
                    json={"query": RUNS_QUERY, "variables": {"runId": run_id}},
                    # Timeout in seconds
                    timeout=3,
                )
                run_status = response.json()["data"]["runOrError"]["status"]
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


class DefaultProxyToDagsterOperator(BaseProxyToDagsterOperator):
    def get_dagster_session(self, context: Context) -> requests.Session:
        return requests.Session()

    def get_dagster_url(self, context: Context) -> str:
        return os.environ["DAGSTER_URL"]


def build_dagster_task(
    original_task: BaseOperator, dagster_operator_klass: Type[BaseProxyToDagsterOperator]
) -> BaseProxyToDagsterOperator:
    return instantiate_dagster_operator(original_task, dagster_operator_klass)


def instantiate_dagster_operator(
    original_task: BaseOperator, dagster_operator_klass: Type[BaseProxyToDagsterOperator]
) -> BaseProxyToDagsterOperator:
    """Instantiates a DagsterOperator as a copy of the provided airflow task.

    We attempt to copy as many of the original task's attributes as possible, while respecting
    that attributes may change between airflow versions. In order to do this, we inspect the
    arguments available to the BaseOperator constructor and copy over any of those arguments that
    are available as attributes on the original task.
    This approach has limitations:
    - If the task attribute is transformed and stored on another property, it will not be copied.
    - If the task attribute is transformed in a way that makes it incompatible with the constructor arg
    and stored in the same property, that will attempt to be copied and potentiall break initialization.
    In the future, if we hit problems with this, we may need to add argument overrides to ensure we either
    attempt to include certain additional attributes, or exclude others. If this continues to be a problem
    across airflow versions, it may be necessary to revise this approach to one that explicitly maps airflow
    version to a set of expected arguments and attributes.
    """
    base_operator_args, base_operator_args_with_defaults = get_params(BaseOperator.__init__)
    init_kwargs = {}

    ignore_args = ["kwargs", "args", "dag"]
    for arg in base_operator_args:
        if arg in ignore_args or getattr(original_task, arg, None) is None:
            continue
        init_kwargs[arg] = getattr(original_task, arg)
    for kwarg, default in base_operator_args_with_defaults.items():
        if kwarg in ignore_args or getattr(original_task, kwarg, None) is None:
            continue
        init_kwargs[kwarg] = getattr(original_task, kwarg, default)

    return dagster_operator_klass(**init_kwargs)


def get_params(func: Callable[..., Any]) -> Tuple[Set[str], Dict[str, Any]]:
    """Retrieves the args and kwargs from the signature of a given function or method.
    For kwargs, default values are retrieved as well.

    Args:
        func (Callable[..., Any]): The function or method to inspect.

    Returns:
        Tuple[Set[str], Dict[str, Any]]:
            - A set of argument names that do not have default values.
            - A dictionary of keyword argument names and their default values.
    """
    # Get the function's signature
    sig = inspect.signature(func)

    # Initialize sets for args without defaults and kwargs with defaults
    args_with_defaults = {}
    args = set()

    # Iterate over function parameters
    for name, param in sig.parameters.items():
        if param.default is inspect.Parameter.empty and name != "self":  # Exclude 'self'
            args.add(name)
        else:
            if name != "self":  # Exclude 'self'
                args_with_defaults[name] = param.default

    return args, args_with_defaults
