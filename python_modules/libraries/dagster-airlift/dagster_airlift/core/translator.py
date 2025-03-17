from typing import TYPE_CHECKING

from dagster import AssetSpec

if TYPE_CHECKING:
    from dagster_airlift.core.serialization.serialized_data import DagInfo


class DagsterAirflowTranslator:
    def get_asset_spec(self, dag_info: "DagInfo") -> AssetSpec:
        from dagster_airlift.core.serialization.defs_construction import (
            dag_description,
            make_default_dag_asset_key,
            peered_dag_asset_metadata,
        )
        from dagster_airlift.core.utils import airflow_kind_dict, dag_kind_dict

        return AssetSpec(
            key=make_default_dag_asset_key(
                instance_name=dag_info.instance_name, dag_id=dag_info.dag_id
            ),
            description=dag_description(dag_info),
            metadata=peered_dag_asset_metadata(dag_info),
            tags={**airflow_kind_dict(), **dag_kind_dict()},
        )
