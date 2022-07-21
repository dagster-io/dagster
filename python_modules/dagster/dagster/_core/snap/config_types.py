import dagster._check as check
from dagster._config import ConfigSchemaSnapshot, snap_from_config_type
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._utils import merge_dicts


def build_config_schema_snapshot(pipeline_def):
    check.inst_param(pipeline_def, "pipeline_def", PipelineDefinition)
    all_config_snaps_by_key = {}
    for mode in pipeline_def.available_modes:
        run_config_schema = pipeline_def.get_run_config_schema(mode)
        all_config_snaps_by_key = merge_dicts(
            all_config_snaps_by_key,
            {ct.key: snap_from_config_type(ct) for ct in run_config_schema.all_config_types()},
        )

    return ConfigSchemaSnapshot(all_config_snaps_by_key)
