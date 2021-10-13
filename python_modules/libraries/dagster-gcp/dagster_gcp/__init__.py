from dagster.core.utils import check_dagster_package_version

from .bigquery.ops import (
    bq_create_dataset,
    bq_delete_dataset,
    bq_op_for_queries,
    bq_solid_for_queries,
    import_df_to_bq,
    import_file_to_bq,
    import_gcs_paths_to_bq,
)
from .bigquery.resources import bigquery_resource
from .bigquery.types import BigQueryError
from .dataproc.ops import dataproc_op, dataproc_solid
from .dataproc.resources import dataproc_resource
from .gcs import GCSFileHandle, gcs_file_manager, gcs_resource
from .version import __version__

check_dagster_package_version("dagster-gcp", __version__)

__all__ = [
    "BigQueryError",
    "GCSFileHandle",
    "bigquery_resource",
    "bq_create_dataset",
    "bq_delete_dataset",
    "bq_op_for_queries",
    "bq_solid_for_queries",
    "dataproc_resource",
    "dataproc_op",
    "dataproc_solid",
    "gcs_resource",
    "gcs_file_manager",
    "import_df_to_bq",
    "import_file_to_bq",
    "import_gcs_paths_to_bq",
]
