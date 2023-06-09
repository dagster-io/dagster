from .asset_defs import (
    load_assets_from_dbt_manifest as load_assets_from_dbt_manifest,
    load_assets_from_dbt_project as load_assets_from_dbt_project,
)
from .asset_selection import DbtManifestAssetSelection as DbtManifestAssetSelection
from .cli import (
    DbtCliClientResource as DbtCliClientResource,
    DbtCliOutput as DbtCliOutput,
    DbtCliResource as DbtCliResource,
    dbt_cli_resource as dbt_cli_resource,
)
from .cloud import (
    DbtCloudClientResource as DbtCloudClientResource,
    DbtCloudOutput as DbtCloudOutput,
    DbtCloudResource as DbtCloudResource,
    DbtCloudResourceV2 as DbtCloudResourceV2,
    dbt_cloud_resource as dbt_cloud_resource,
    dbt_cloud_run_op as dbt_cloud_run_op,
    load_assets_from_dbt_cloud_job as load_assets_from_dbt_cloud_job,
)
from .dbt_resource import DbtResource as DbtResource
from .errors import (
    DagsterDbtCliFatalRuntimeError as DagsterDbtCliFatalRuntimeError,
    DagsterDbtCliHandledRuntimeError as DagsterDbtCliHandledRuntimeError,
    DagsterDbtCliOutputsNotFoundError as DagsterDbtCliOutputsNotFoundError,
    DagsterDbtCliRuntimeError as DagsterDbtCliRuntimeError,
    DagsterDbtCliUnexpectedOutputError as DagsterDbtCliUnexpectedOutputError,
    DagsterDbtCloudJobInvariantViolationError as DagsterDbtCloudJobInvariantViolationError,
    DagsterDbtError as DagsterDbtError,
)
from .ops import (
    dbt_build_op as dbt_build_op,
    dbt_compile_op as dbt_compile_op,
    dbt_docs_generate_op as dbt_docs_generate_op,
    dbt_ls_op as dbt_ls_op,
    dbt_run_op as dbt_run_op,
    dbt_seed_op as dbt_seed_op,
    dbt_snapshot_op as dbt_snapshot_op,
    dbt_test_op as dbt_test_op,
)
from .types import DbtOutput as DbtOutput
from .version import __version__ as __version__

# isort: split

# ########################
# ##### DYNAMIC IMPORTS
# ########################
import importlib
from typing import TYPE_CHECKING, Any, Mapping, Sequence, Tuple

from dagster._core.libraries import DagsterLibraryRegistry
from dagster._utils.backcompat import deprecation_warning
from typing_extensions import Final

DagsterLibraryRegistry.register("dagster-dbt", __version__)

if TYPE_CHECKING:
    ##### EXAMPLE
    # from dagster.some.module import (
    #     Foo as Foo,
    # )

    ##### Deprecating dbt-rpc
    from .errors import (
        DagsterDbtRpcUnexpectedPollOutputError as DagsterDbtRpcUnexpectedPollOutputError,
    )
    from .rpc import (
        DbtRpcResource as DbtRpcResource,
        DbtRpcSyncResource as DbtRpcSyncResource,
        dbt_rpc_resource as dbt_rpc_resource,
        dbt_rpc_sync_resource as dbt_rpc_sync_resource,
        local_dbt_rpc_resource as local_dbt_rpc_resource,
    )

_DEPRECATED: Final[Mapping[str, Tuple[str, str, str]]] = {
    ##### EXAMPLE
    # "Foo": (
    #     "dagster.some.module",
    #     "1.1.0",  # breaking version
    #     "Use Bar instead.",
    # ),
    ##### Deprecating dbt-rpc
    **{
        value: (
            module,
            "0.20.0",
            "dbt-rpc is deprecated: https://github.com/dbt-labs/dbt-rpc.",
        )
        for value, module in [
            ("DbtRpcOutput", "dagster_dbt.rpc"),
            ("DbtRpcResource", "dagster_dbt.rpc"),
            ("DbtRpcSyncResource", "dagster_dbt.rpc"),
            ("dbt_rpc_resource", "dagster_dbt.rpc"),
            ("dbt_rpc_sync_resource", "dagster_dbt.rpc"),
            ("local_dbt_rpc_resource", "dagster_dbt.rpc"),
            ("DagsterDbtRpcUnexpectedPollOutputError", "dagster_dbt.errors"),
        ]
    },
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED:
        module, breaking_version, additional_warn_text = _DEPRECATED[name]
        value = getattr(importlib.import_module(module), name)
        deprecation_warning(name, breaking_version, additional_warn_text)
        return value
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> Sequence[str]:
    return [*globals(), *_DEPRECATED.keys()]
