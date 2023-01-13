from dagster._core.utils import check_dagster_package_version

from .redshift_pandas_type_handler import (
    RedshiftPandasTypeHandler as RedshiftPandasTypeHandler,
    redshift_pandas_io_manager as redshift_pandas_io_manager,
)
from .version import __version__ as __version__

check_dagster_package_version("dagster-redshift-pandas", __version__)
