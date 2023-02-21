from dagster._core.libraries import DagsterLibraryRegistry

from .bigquery.io_manager import build_bigquery_io_manager as build_bigquery_io_manager
from .bigquery.ops import (
    bq_create_dataset as bq_create_dataset,
    bq_delete_dataset as bq_delete_dataset,
    bq_op_for_queries as bq_op_for_queries,
    import_df_to_bq as import_df_to_bq,
    import_file_to_bq as import_file_to_bq,
    import_gcs_paths_to_bq as import_gcs_paths_to_bq,
)
from .bigquery.resources import bigquery_resource as bigquery_resource
from .bigquery.types import BigQueryError as BigQueryError
from .dataproc.ops import dataproc_op as dataproc_op
from .dataproc.resources import dataproc_resource as dataproc_resource
from .gcs import (
    GCSFileHandle as GCSFileHandle,
    gcs_file_manager as gcs_file_manager,
    gcs_resource as gcs_resource,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-gcp", __version__)
