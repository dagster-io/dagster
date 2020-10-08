from dagster.core.utils import check_dagster_package_version

from .flyte_compiler import DagsterFlyteCompiler, compile_pipeline_to_flyte
from .version import __version__

check_dagster_package_version("dagster-flyte", __version__)
