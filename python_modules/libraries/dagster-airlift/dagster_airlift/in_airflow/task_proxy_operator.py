import inspect
import json
import os
from collections.abc import Iterable, Mapping, Sequence
from typing import Any, Callable

import requests
from airflow.models import BaseOperator

from dagster_airlift.constants import TASK_MAPPING_METADATA_KEY
from dagster_airlift.in_airflow.base_asset_operator import BaseDagsterAssetsOperator, Context


class BaseProxyTaskToDagsterOperator(BaseDagsterAssetsOperator):
    """An operator that proxies task execution to Dagster assets with metadata that map to this task's dag ID and task ID.

    For the DAG ID and task ID that this operator proxies, it expects there to be corresponding assets
    in the linked Dagster deployment that have metadata entries with the key `dagster-airlift/task-mapping` that
    map to this DAG ID and task ID. This metadata is typically set using the
    :py:func:`dagster_airlift.core.assets_with_task_mappings` function.

    The following methods must be implemented by subclasses:

        - :py:meth:`get_dagster_session` (inherited from :py:class:`BaseDagsterAssetsOperator`)
        - :py:meth:`get_dagster_url` (inherited from :py:class:`BaseDagsterAssetsOperator`)
        - :py:meth:`build_from_task` A class method which takes the task to be proxied, and constructs
            an instance of this operator from it.

    There is a default implementation of this operator, :py:class:`DefaultProxyTaskToDagsterOperator`,
    which is used by :py:func:`proxying_to_dagster` if no override operator is provided.
    """

    def filter_asset_nodes(
        self, context: Context, asset_nodes: Sequence[Mapping[str, Any]]
    ) -> Iterable[Mapping[str, Any]]:
        for asset_node in asset_nodes:
            if matched_dag_id_task_id(
                asset_node, self.get_airflow_dag_id(context), self.get_airflow_task_id(context)
            ):
                yield asset_node

    @classmethod
    def build_from_task(cls, task: BaseOperator) -> "BaseProxyTaskToDagsterOperator":
        return build_dagster_task(task, cls)


class DefaultProxyTaskToDagsterOperator(BaseProxyTaskToDagsterOperator):
    """The default task proxying operator - which opens a blank session and expects the dagster URL to be set in the environment.
    The dagster url is expected to be set in the environment as DAGSTER_URL.

    This operator should not be instantiated directly - it is instantiated by :py:func:`proxying_to_dagster` if no
    override operator is provided.
    """

    def get_dagster_session(self, context: Context) -> requests.Session:
        return requests.Session()

    def get_dagster_url(self, context: Context) -> str:
        return os.environ["DAGSTER_URL"]


def build_dagster_task(
    original_task: BaseOperator,
    dagster_operator_klass: type[BaseProxyTaskToDagsterOperator],
) -> BaseProxyTaskToDagsterOperator:
    return instantiate_dagster_operator(original_task, dagster_operator_klass)


def instantiate_dagster_operator(
    original_task: BaseOperator,
    dagster_operator_klass: type[BaseProxyTaskToDagsterOperator],
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

    ignore_args = [
        # These don't make sense in context to copy
        "kwargs",
        "args",
        "dag",
        # The weight rule stored on the base operator is a private subclass of PriorityWeightStrategy,
        # which satisfies the type signature of the constructor, but fails the validation process in
        # the constructor. See https://github.com/apache/airflow/blob/2b15e9f26fee27b6c1fbc8167d0e0558198ffa7a/airflow/task/priority_strategy.py#L127
        # for more details.
        # We could likely add custom handling here to support the parameter.
        # For now, we ignore it, as it's currently an experimental feature in Airflow.
        "weight_rule",
    ]
    for arg in base_operator_args:
        if arg in ignore_args or getattr(original_task, arg, None) is None:
            continue
        init_kwargs[arg] = getattr(original_task, arg)
    for kwarg, default in base_operator_args_with_defaults.items():
        if kwarg in ignore_args or getattr(original_task, kwarg, None) is None:
            continue
        init_kwargs[kwarg] = getattr(original_task, kwarg, default)

    # Make sure that the operator overrides take precedence.

    return dagster_operator_klass(**init_kwargs)


def get_params(func: Callable[..., Any]) -> tuple[set[str], dict[str, Any]]:
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

    mapping_entry = json_metadata_entries.get(TASK_MAPPING_METADATA_KEY)
    if mapping_entry:
        task_handle_dict_list = json.loads(mapping_entry)
        for task_handle_dict in task_handle_dict_list:
            if task_handle_dict["dag_id"] == dag_id and task_handle_dict["task_id"] == task_id:
                return True

    return False
