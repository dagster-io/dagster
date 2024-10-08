import inspect
import json
import os
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence, Set, Tuple, Type

import requests
from airflow.models.operator import BaseOperator
from airflow.utils.context import Context

from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.in_airflow.base_asset_operator import BaseDagsterAssetsOperator


class BaseProxyTaskToDagsterOperator(BaseDagsterAssetsOperator):
    """An operator that proxies task execution to Dagster assets with metadata that map to this task's dag ID and task ID."""

    def filter_asset_nodes(
        self, context: Context, asset_nodes: Sequence[Mapping[str, Any]]
    ) -> Iterable[Mapping[str, Any]]:
        for asset_node in asset_nodes:
            if matched_dag_id_task_id(
                asset_node, self.get_airflow_dag_id(context), self.get_airflow_task_id(context)
            ):
                yield asset_node


class DefaultProxyTaskToDagsterOperator(BaseProxyTaskToDagsterOperator):
    """The default task proxying operator - which opens a blank session and expects the dagster URL to be set in the environment.
    The dagster url is expected to be set in the environment as DAGSTER_URL.
    """

    def get_dagster_session(self, context: Context) -> requests.Session:
        return requests.Session()

    def get_dagster_url(self, context: Context) -> str:
        return os.environ["DAGSTER_URL"]


def build_dagster_task(
    original_task: BaseOperator, dagster_operator_klass: Type[BaseProxyTaskToDagsterOperator]
) -> BaseProxyTaskToDagsterOperator:
    return instantiate_dagster_operator(original_task, dagster_operator_klass)


def instantiate_dagster_operator(
    original_task: BaseOperator, dagster_operator_klass: Type[BaseProxyTaskToDagsterOperator]
) -> BaseProxyTaskToDagsterOperator:
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


def matched_dag_id_task_id(asset_node: Mapping[str, Any], dag_id: str, task_id: str) -> bool:
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
