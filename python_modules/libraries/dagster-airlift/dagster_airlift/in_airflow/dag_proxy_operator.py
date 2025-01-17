import json
import os
from abc import abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

import requests
from airflow import DAG

from dagster_airlift.constants import DAG_MAPPING_METADATA_KEY
from dagster_airlift.in_airflow.base_asset_operator import BaseDagsterAssetsOperator, Context


class BaseProxyDAGToDagsterOperator(BaseDagsterAssetsOperator):
    """An operator base class that proxies the entire DAG's execution to Dagster assets with
    metadata that map to the DAG id used by this task.

    For the Dag ID that this operator proxies, it expects there to be corresponding assets
    in the linked Dagster deployment that have metadata entries with the key `dagster-airlift/dag-mapping` that
    map to this Dag ID. This metadata is typically set using the
    :py:func:`dagster_airlift.core.assets_with_dag_mappings` function.

    The following methods must be implemented by subclasses:

        - :py:meth:`get_dagster_session` (inherited from :py:class:`BaseDagsterAssetsOperator`)
        - :py:meth:`get_dagster_url` (inherited from :py:class:`BaseDagsterAssetsOperator`)
        - :py:meth:`build_from_dag` A class method which takes the DAG to be proxied, and constructs
            an instance of this operator from it.

    There is a default implementation of this operator, :py:class:`DefaultProxyDAGToDagsterOperator`,
    which is used by :py:func:`proxying_to_dagster` if no override operator is provided.
    """

    def filter_asset_nodes(
        self, context: Context, asset_nodes: Sequence[Mapping[str, Any]]
    ) -> Iterable[Mapping[str, Any]]:
        for asset_node in asset_nodes:
            if matched_dag_id(asset_node, self.get_airflow_dag_id(context)):
                yield asset_node

    @classmethod
    @abstractmethod
    def build_from_dag(cls, dag: DAG) -> "BaseProxyDAGToDagsterOperator":
        """Builds a proxy operator from the passed-in DAG."""


class DefaultProxyDAGToDagsterOperator(BaseProxyDAGToDagsterOperator):
    """The default task proxying operator - which opens a blank session and expects the dagster URL to be set in the environment.
    The dagster url is expected to be set in the environment as DAGSTER_URL.

    This operator should not be instantiated directly - it is instantiated by :py:func:`proxying_to_dagster` if no
    override operator is provided.
    """

    def get_dagster_session(self, context: Context) -> requests.Session:
        return requests.Session()

    def get_dagster_url(self, context: Context) -> str:
        return os.environ["DAGSTER_URL"]

    @classmethod
    def build_from_dag(cls, dag: DAG) -> "DefaultProxyDAGToDagsterOperator":
        return DefaultProxyDAGToDagsterOperator(
            task_id=f"DAGSTER_OVERRIDE_DAG_{dag.dag_id}",
            dag=dag,
        )


def matched_dag_id(asset_node: Mapping[str, Any], dag_id: str) -> bool:
    json_metadata_entries = {
        entry["label"]: entry["jsonString"]
        for entry in asset_node["metadataEntries"]
        if entry["__typename"] == "JsonMetadataEntry"
    }

    mapping_entry = json_metadata_entries.get(DAG_MAPPING_METADATA_KEY)
    if mapping_entry:
        mappings = json.loads(mapping_entry)
        return any(mapping["dag_id"] == dag_id for mapping in mappings)
    return False
