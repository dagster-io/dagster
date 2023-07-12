from .asset_defs import (
    load_assets_from_dbt_manifest as load_assets_from_dbt_manifest,
    load_assets_from_dbt_project as load_assets_from_dbt_project,
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
from .errors import (
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
from .version import __version__ as __version__

# ruff: isort: split

# ########################
# ##### EXPERIMENTAL IMPORTS
# ########################

from .asset_decorator import dbt_assets as dbt_assets
from .core import (
    DbtCli as DbtCli,
    DbtCliEventMessage as DbtCliEventMessage,
    DbtCliInvocation as DbtCliInvocation,
    DbtManifest as DbtManifest,
    DbtManifestAssetSelection as DbtManifestAssetSelection,
)

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

    # isort: split
    ##### Deprecating DbtCliClientResource
    from .core import (
        DbtCliClientResource as DbtCliClientResource,
        DbtCliOutput as DbtCliOutput,
        DbtCliResource as DbtCliResource,
        dbt_cli_resource as dbt_cli_resource,
    )
    from .dbt_resource import DbtResource as DbtResource
    from .errors import (
        DagsterDbtCliFatalRuntimeError as DagsterDbtCliFatalRuntimeError,
        DagsterDbtCliHandledRuntimeError as DagsterDbtCliHandledRuntimeError,
        DagsterDbtCliOutputsNotFoundError as DagsterDbtCliOutputsNotFoundError,
    )
    from .types import DbtOutput as DbtOutput

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
    **{
        value: (
            module,
            "0.21.0",
            additional_warn_text,
        )
        for value, module, additional_warn_text in [
            (
                "DbtCliClientResource",
                "dagster_dbt.core",
                "DbtCliClientResource is deprecated. Use DbtCli instead.",
            ),
            ("DbtCliOutput", "dagster_dbt.core", None),
            (
                "DbtCliResource",
                "dagster_dbt.core",
                "DbtCliResource is deprecated. Use DbtCli instead.",
            ),
            (
                "dbt_cli_resource",
                "dagster_dbt.core",
                "dbt_cli_resource is deprecated. Use DbtCli instead.",
            ),
            (
                "DbtResource",
                "dagster_dbt.dbt_resource",
                "DbtResource is deprecated. Use DbtCli instead.",
            ),
            ("DagsterDbtCliFatalRuntimeError", "dagster_dbt.errors", None),
            ("DagsterDbtCliHandledRuntimeError", "dagster_dbt.errors", None),
            ("DagsterDbtCliOutputsNotFoundError", "dagster_dbt.errors", None),
            ("DbtOutput", "dagster_dbt.types", None),
        ]
    },
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED:
        module, breaking_version, additional_warn_text = _DEPRECATED[name]
        if additional_warn_text:
            deprecation_warning(name, breaking_version, additional_warn_text)

        value = getattr(importlib.import_module(module), name)

        return value
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> Sequence[str]:
    return [*globals(), *_DEPRECATED.keys()]
