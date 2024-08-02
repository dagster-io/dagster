SDF_EXECUTABLE = "sdf"
SDF_TARGET_DIR = "sdftarget"
SDF_DAGSTER_OUTPUT_DIR = "sdf_dagster_out"
SDF_INFORMATION_SCHEMA_TABLES_STAGE_COMPILE = [
    "tables",
    "columns",
    "table_lineage",
    "column_lineage",
]
SDF_INFORMATION_SCHEMA_TABLES_STAGE_PARSE = ["table_deps"]
DEFAULT_SDF_WORKSPACE_ENVIRONMENT = "dbg"
SDF_WORKSPACE_YML = "workspace.sdf.yml"
