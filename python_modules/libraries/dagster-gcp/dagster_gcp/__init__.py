from dagster._core.libraries import DagsterLibraryRegistry

from .gcs import (
    GCSResource as GCSResource,
    GCSFileHandle as GCSFileHandle,
    GCSFileManagerResource as GCSFileManagerResource,
    gcs_resource as gcs_resource,
    gcs_file_manager as gcs_file_manager,
)
from .version import __version__
from .bigquery.ops import (
    import_df_to_bq as import_df_to_bq,
    bq_create_dataset as bq_create_dataset,
    bq_delete_dataset as bq_delete_dataset,
    bq_op_for_queries as bq_op_for_queries,
    import_file_to_bq as import_file_to_bq,
    import_gcs_paths_to_bq as import_gcs_paths_to_bq,
)
from .dataproc.ops import (
    DataprocOpConfig as DataprocOpConfig,
    dataproc_op as dataproc_op,
    configurable_dataproc_op as configurable_dataproc_op,
)
from .bigquery.types import BigQueryError as BigQueryError
from .gcs.io_manager import (
    GCSPickleIOManager as GCSPickleIOManager,
    ConfigurablePickledObjectGCSIOManager as ConfigurablePickledObjectGCSIOManager,
    gcs_pickle_io_manager as gcs_pickle_io_manager,
)
from .bigquery.resources import (
    BigQueryResource as BigQueryResource,
    bigquery_resource as bigquery_resource,
    fetch_last_updated_timestamps as fetch_last_updated_timestamps,
)
from .dataproc.resources import (
    DataprocResource as DataprocResource,
    dataproc_resource as dataproc_resource,
)
from .bigquery.io_manager import (
    BigQueryIOManager as BigQueryIOManager,
    build_bigquery_io_manager as build_bigquery_io_manager,
)

DagsterLibraryRegistry.register("dagster-gcp", __version__)
