import dagster._check as check
from dagster._config import ConfigSchemaSnapshot, snap_from_config_type
from dagster._core.definitions.job_definition import JobDefinition


def build_config_schema_snapshot(pipeline_def: JobDefinition) -> ConfigSchemaSnapshot:
    check.inst_param(pipeline_def, "pipeline_def", JobDefinition)
    config_snaps_by_key = {
        ct.key: snap_from_config_type(ct)
        for ct in pipeline_def.run_config_schema.all_config_types()
    }
    return ConfigSchemaSnapshot(config_snaps_by_key)
