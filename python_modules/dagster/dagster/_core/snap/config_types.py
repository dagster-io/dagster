import dagster._check as check
from dagster._config import ConfigSchemaSnapshot, snap_from_config_type
from dagster._core.definitions.job_definition import JobDefinition


def build_config_schema_snapshot(job_def: JobDefinition) -> ConfigSchemaSnapshot:
    check.inst_param(job_def, "job_def", JobDefinition)
    return ConfigSchemaSnapshot(
        all_config_snaps_by_key={
            ct.key: snap_from_config_type(ct) for ct in job_def.run_config_schema.all_config_types()
        }
    )
