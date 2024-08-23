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

DAGSTER_SDF_TABLE_ID = "dagster_sdf/table_id"
DAGSTER_SDF_CATALOG_NAME = "dagster_sdf/catalog"
DAGSTER_SDF_SCHEMA_NAME = "dagster_sdf/schema"
DAGSTER_SDF_TABLE_NAME = "dagster_sdf/table_name"
DAGSTER_SDF_PURPOSE = "dagster_sdf/purpose"
DAGSTER_SDF_DIALECT = "dagster_sdf/dialect"
