import inspect
import json
import logging
import os
from abc import ABC, abstractmethod
from collections import defaultdict
from functools import lru_cache
from typing import (
    AbstractSet,
    Any,
    Callable,
    Dict,
    List,
    Mapping,
    Sequence,
    Set,
    Tuple,
    Type,
    TypedDict,
    cast,
)

import requests
from airflow.models.dagrun import DagRun
from airflow.models.operator import BaseOperator
from airflow.operators.python import get_current_context
from airflow.utils.context import Context
from requests import Response

from dagster_airlift.constants import (
    DAG_ID_TAG_KEY,
    DAG_RUN_ID_TAG_KEY,
    TASK_ID_TAG_KEY,
    TASK_MAPPING_METADATA_KEY,
)

from .gql_queries import ASSET_NODES_QUERY, RUNS_QUERY, TRIGGER_ASSETS_MUTATION, VERIFICATION_QUERY

logger = logging.getLogger(__name__)


class ExecutableAssetIdentifier(TypedDict):
    location_name: str
    repository_name: str
    asset_key_path: Sequence[str]
    job_name: str


JobIdentifier = Tuple[str, str, str]


def matched_dag_id_task_id(asset_node: dict, dag_id: str, task_id: str) -> bool:
    json_metadata_entries = {
        entry["label"]: entry["jsonString"]
        for entry in asset_node["metadataEntries"]
        if entry["__typename"] == "JsonMetadataEntry"
    }

    if mapping_entry := json_metadata_entries.get(TASK_MAPPING_METADATA_KEY):
        task_handle_dict_list = json.loads(mapping_entry)
        for task_handle_dict in task_handle_dict_list:
            if task_handle_dict["dag_id"] == dag_id and task_handle_dict["task_id"] == task_id:
                return True

    return False


class BaseProxyToDagsterOperator(BaseOperator, ABC):
    """Interface for a DagsterOperator.

    This interface is used to create a custom operator that will be used to replace the original airflow operator when a task is marked as proxied.
    """

    @abstractmethod
    def get_dagster_session(self) -> requests.Session:
        """Returns a requests session that can be used to make requests to the Dagster API."""

    @abstractmethod
    def get_dagster_url(self) -> str:
        """Returns the URL for the Dagster instance."""

    @abstractmethod
    def get_assets_to_trigger(self) -> Sequence[ExecutableAssetIdentifier]:
        """Returns the assets to trigger for the given task."""

    def _get_validated_session(self) -> requests.Session:
        session = self.get_dagster_session()
        dagster_url = self.get_dagster_url()
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

    def get_dag_run(self) -> DagRun:
        context = get_current_context()
        if "dag_run" not in context:
            raise Exception("Dag run not found in context. Expected to find dag_run.")
        return context["dag_run"]

    def get_dag_id(self) -> str:
        return self.get_dag_run().dag_id  # type: ignore # thinks it's a column due to django syntax

    def get_dag_run_id(self) -> str:
        return self.get_dag_run().run_id  # type: ignore # thinks it's a column due to django syntax

    def get_task_id(self) -> str:
        context = get_current_context()
        if "task" not in context:
            raise Exception("Task not found in context. Expected to find task.")
        return context["task"].task_id

    def get_dagster_run_tags(self) -> Mapping[str, str]:
        dag_run = self.get_dag_run()
        return {
            DAG_ID_TAG_KEY: cast(str, dag_run.dag_id),
            DAG_RUN_ID_TAG_KEY: cast(str, dag_run.run_id),
            TASK_ID_TAG_KEY: self.get_task_id(),
        }

    @lru_cache(maxsize=1)
    def get_all_asset_nodes(self) -> Sequence[Dict[str, Any]]:
        """Returns all asset nodes retrieved from the Dagster graphql API.
        We cache the result after the first call.
        """
        dagster_url = self.get_dagster_url()
        response = self.get_dagster_session().post(
            # Timeout in seconds
            f"{dagster_url}/graphql",
            json={"query": ASSET_NODES_QUERY},
            timeout=3,
        )
        return self.get_valid_graphql_response(response, "assetNodes")

    def _build_asset_identifier_from_asset_node(
        self, asset_node: Dict[str, Any]
    ) -> ExecutableAssetIdentifier:
        return {
            "location_name": asset_node["jobs"][0]["repository"]["location"]["name"],
            "repository_name": asset_node["jobs"][0]["repository"]["name"],
            "asset_key_path": asset_node["assetKey"]["path"],
            "job_name": asset_node["jobs"][0]["name"],
        }

    def trigger_run(self, execution_params: Dict[str, Any]) -> str:
        """Triggers a run in Dagster."""
        session = self.get_dagster_session()
        dagster_url = self.get_dagster_url()
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

    def trigger_runs_for_assets(
        self, executable_assets: Sequence[ExecutableAssetIdentifier]
    ) -> AbstractSet[str]:
        """Triggers runs for the given assets in Dagster."""
        assets_grouped_by_job_identifier = _group_assets_by_job_identifier(executable_assets)
        triggered_runs = set()
        for (
            location_name,
            repository_name,
            job_name,
        ), asset_key_paths in assets_grouped_by_job_identifier.items():
            user_friendly_asset_paths = [
                "/".join(asset_key_path) for asset_key_path in asset_key_paths
            ]
            logger.debug(
                f"Triggering run for {location_name}/{repository_name}/{job_name} with assets {user_friendly_asset_paths}"
            )
            run_id = self.trigger_run(
                _build_execution_params(
                    self.get_dagster_run_tags(),
                    asset_key_paths,
                    location_name,
                    repository_name,
                    job_name,
                )
            )
            logger.debug(f"Launched run {run_id}...")
            triggered_runs.add(run_id)
        return triggered_runs

    def _get_dagster_run_status(self, run_id: str) -> str:
        session = self._get_validated_session()
        response = session.post(
            f"{self.get_dagster_url()}/graphql",
            json={"query": RUNS_QUERY, "variables": {"runId": run_id}},
            # Timeout in seconds
            timeout=3,
        )
        return self.get_valid_graphql_response(response, "runOrError")["status"]

    def wait_for_runs_to_complete(self, run_ids: AbstractSet[str]) -> None:
        completed_runs = {}  # key is run_id, value is status
        while len(completed_runs) < len(run_ids):
            for run_id in run_ids:
                if run_id in completed_runs:
                    continue
                run_status = self._get_dagster_run_status(run_id)
                if run_status in ["SUCCESS", "FAILURE", "CANCELED"]:
                    logger.debug(f"Run {run_id} completed with status {run_status}")
                    completed_runs[run_id] = run_status
        non_successful_runs = [
            run_id for run_id, status in completed_runs.items() if status != "SUCCESS"
        ]
        if len(non_successful_runs) > 0:
            raise Exception(f"Runs {non_successful_runs} did not complete successfully.")
        logger.debug("All runs completed successfully.")

    def get_valid_graphql_response(self, response: Response, key: str) -> Any:
        response_json = response.json()
        if not response_json.get("data"):
            raise Exception(f"Error in GraphQL request. No data key: {response_json}")

        if key not in response_json["data"]:
            raise Exception(f"Error in GraphQL request. No {key} key: {response_json}")

        return response_json["data"][key]

    def _execute_proxied_dagster_runs(self, context: Context) -> None:
        assets = self.get_assets_to_trigger()
        triggered_runs = self.trigger_runs_for_assets(assets)
        self.wait_for_runs_to_complete(triggered_runs)

    def execute(self, context: Context) -> Any:
        # https://github.com/apache/airflow/discussions/24463
        os.environ["NO_PROXY"] = "*"
        self._execute_proxied_dagster_runs(context)


def _group_assets_by_job_identifier(
    assets: Sequence[ExecutableAssetIdentifier],
) -> Mapping[JobIdentifier, Sequence[Sequence[str]]]:
    assets_by_job_identifier: Dict[JobIdentifier, List[Sequence[str]]] = defaultdict(list)
    for asset in assets:
        assets_by_job_identifier[
            (asset["location_name"], asset["repository_name"], asset["job_name"])
        ].append(asset["asset_key_path"])
    return assets_by_job_identifier


def _build_execution_params(
    tags: Mapping[str, str],
    asset_key_paths: Sequence[Sequence[str]],
    location_name: str,
    repository_name: str,
    job_name: str,
) -> Dict[str, Any]:
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
            "assetSelection": [{"path": asset_key_path} for asset_key_path in asset_key_paths],
            "assetCheckSelection": [],
        },
    }


class DefaulProxyToDagsterOperator(BaseProxyToDagsterOperator):
    """Underlying implementation of a DagsterOperator. This one uses the DAGSTER_URL environment variable to connect to the Dagster instance."""

    @lru_cache(maxsize=1)
    def get_dagster_session(self) -> requests.Session:
        return requests.Session()

    def get_dagster_url(self) -> str:
        return os.environ["DAGSTER_URL"]


class ProxiedTaskDagsterOperator(DefaulProxyToDagsterOperator):
    """Operator that executes tasks that have been proxied to Dagster.
    This operator will find all assets that are mapped to this task and trigger runs for them.
    """

    def get_assets_to_trigger(self, context: Context) -> Sequence[ExecutableAssetIdentifier]:
        dag_id = self.get_dag_id()
        task_id = self.get_task_id()
        executable_assets = []
        for asset_node in self.get_all_asset_nodes(self.get_dagster_session()):
            if matched_dag_id_task_id(asset_node, dag_id, task_id):
                executable_assets.append(self._build_asset_identifier_from_asset_node(asset_node))
        return executable_assets


class StandaloneAssetsDagsterOperator(DefaulProxyToDagsterOperator):
    """Operator that triggers runs for a set of provided assets."""

    def __init__(self, asset_key_paths: Sequence[Sequence[str]], **kwargs):
        super().__init__(**kwargs)
        self.asset_key_paths = asset_key_paths

    def get_assets_to_trigger(self) -> Sequence[ExecutableAssetIdentifier]:
        executable_assets = []
        for node in self.get_all_asset_nodes(self.get_dagster_session()):
            if node["assetKey"]["path"] in self.asset_key_paths:
                executable_assets.append(self._build_asset_identifier_from_asset_node(node))
        return executable_assets


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
