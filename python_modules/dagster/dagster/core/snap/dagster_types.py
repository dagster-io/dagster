from collections import namedtuple

from dagster import check
from dagster.core.definitions.pipeline import PipelineDefinition
from dagster.core.types.dagster_type import DagsterType, DagsterTypeKind
from dagster.serdes import whitelist_for_serdes


def build_dagster_type_namespace_snapshot(pipeline_def):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    return DagsterTypeNamespaceSnapshot(
        {dt.key: build_dagster_type_snap(dt) for dt in pipeline_def.all_dagster_types()}
    )


def build_dagster_type_snap(dagster_type):
    check.inst_param(dagster_type, "dagster_type", DagsterType)
    return DagsterTypeSnap(
        kind=dagster_type.kind,
        key=dagster_type.key,
        name=dagster_type.unique_name if dagster_type.has_unique_name else None,
        display_name=dagster_type.display_name,
        description=dagster_type.description,
        is_builtin=dagster_type.is_builtin,
        type_param_keys=dagster_type.type_param_keys,
        loader_schema_key=dagster_type.loader_schema_key,
        materializer_schema_key=dagster_type.materializer_schema_key,
    )


@whitelist_for_serdes
class DagsterTypeNamespaceSnapshot(
    namedtuple("_DagsterTypeNamespaceSnapshot", "all_dagster_type_snaps_by_key")
):
    def __new__(cls, all_dagster_type_snaps_by_key):
        return super(DagsterTypeNamespaceSnapshot, cls).__new__(
            cls,
            all_dagster_type_snaps_by_key=check.dict_param(
                all_dagster_type_snaps_by_key,
                "all_dagster_type_snaps_by_key",
                key_type=str,
                value_type=DagsterTypeSnap,
            ),
        )

    def get_dagster_type_snap(self, key):
        check.str_param(key, "key")
        return self.all_dagster_type_snaps_by_key[key]


@whitelist_for_serdes
class DagsterTypeSnap(
    namedtuple(
        "_DagsterTypeSnap",
        "kind key name description display_name is_builtin type_param_keys "
        "loader_schema_key materializer_schema_key ",
    )
):
    def __new__(
        cls,
        kind,
        key,
        name,
        description,
        display_name,
        is_builtin,
        type_param_keys,
        loader_schema_key=None,
        materializer_schema_key=None,
    ):
        return super(DagsterTypeSnap, cls).__new__(
            cls,
            kind=check.inst_param(kind, "kind", DagsterTypeKind),
            key=check.str_param(key, "key"),
            name=check.opt_str_param(name, "name"),
            display_name=check.str_param(display_name, "display_name"),
            description=check.opt_str_param(description, "description"),
            is_builtin=check.bool_param(is_builtin, "is_builtin"),
            type_param_keys=check.list_param(type_param_keys, "type_param_keys", of_type=str),
            loader_schema_key=check.opt_str_param(loader_schema_key, "loader_schema_key"),
            materializer_schema_key=check.opt_str_param(
                materializer_schema_key, "materializer_schema_key"
            ),
        )
