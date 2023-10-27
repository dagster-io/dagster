from dagster._core.libraries import DagsterLibraryRegistry

from .bigquery.io_manager import (
    BigQueryIOManager as BigQueryIOManager,
    build_bigquery_io_manager as build_bigquery_io_manager,
)
from .bigquery.ops import (
    bq_create_dataset as bq_create_dataset,
    bq_delete_dataset as bq_delete_dataset,
    bq_op_for_queries as bq_op_for_queries,
    import_df_to_bq as import_df_to_bq,
    import_file_to_bq as import_file_to_bq,
    import_gcs_paths_to_bq as import_gcs_paths_to_bq,
)
from .bigquery.resources import (
    BigQueryResource as BigQueryResource,
    bigquery_resource as bigquery_resource,
)
from .bigquery.types import BigQueryError as BigQueryError
from .dataproc.ops import (
    DataprocOpConfig as DataprocOpConfig,
    configurable_dataproc_op as configurable_dataproc_op,
    dataproc_op as dataproc_op,
)
from .dataproc.resources import (
    DataprocResource as DataprocResource,
    dataproc_resource as dataproc_resource,
)
from .gcs import (
    GCSFileHandle as GCSFileHandle,
    GCSFileManagerResource as GCSFileManagerResource,
    GCSResource as GCSResource,
    gcs_file_manager as gcs_file_manager,
    gcs_resource as gcs_resource,
)
from .gcs.io_manager import (
    ConfigurablePickledObjectGCSIOManager as ConfigurablePickledObjectGCSIOManager,
    GCSPickleIOManager as GCSPickleIOManager,
    gcs_pickle_io_manager as gcs_pickle_io_manager,
)
from .version import __version__

DagsterLibraryRegistry.register("dagster-gcp", __version__)
