from .asset_decorator import dbt_assets as dbt_assets
from .asset_specs import build_dbt_asset_specs as build_dbt_asset_specs
from .asset_utils import (
    build_dbt_asset_selection as build_dbt_asset_selection,
    build_schedule_from_dbt_selection as build_schedule_from_dbt_selection,
    default_group_from_dbt_resource_props as default_group_from_dbt_resource_props,
    default_metadata_from_dbt_resource_props as default_metadata_from_dbt_resource_props,
    get_asset_key_for_model as get_asset_key_for_model,
    get_asset_key_for_source as get_asset_key_for_source,
    get_asset_keys_by_output_name_for_source as get_asset_keys_by_output_name_for_source,
    group_from_dbt_resource_props_fallback_to_directory as group_from_dbt_resource_props_fallback_to_directory,
)
from .cloud import (
    DbtCloudClientResource as DbtCloudClientResource,
    DbtCloudOutput as DbtCloudOutput,
    DbtCloudResource as DbtCloudResource,
    dbt_cloud_resource as dbt_cloud_resource,
    dbt_cloud_run_op as dbt_cloud_run_op,
    load_assets_from_dbt_cloud_job as load_assets_from_dbt_cloud_job,
)
from .core import (
    DbtCliEventMessage as DbtCliEventMessage,
    DbtCliInvocation as DbtCliInvocation,
    DbtCliResource as DbtCliResource,
)
from .dagster_dbt_translator import (
    DagsterDbtTranslator as DagsterDbtTranslator,
    DagsterDbtTranslatorSettings as DagsterDbtTranslatorSettings,
    KeyPrefixDagsterDbtTranslator as KeyPrefixDagsterDbtTranslator,
)
from .dbt_manifest_asset_selection import DbtManifestAssetSelection as DbtManifestAssetSelection
from .dbt_project import DbtProject as DbtProject
from .errors import (
    DagsterDbtCliRuntimeError as DagsterDbtCliRuntimeError,
    DagsterDbtCliUnexpectedOutputError as DagsterDbtCliUnexpectedOutputError,
    DagsterDbtCloudJobInvariantViolationError as DagsterDbtCloudJobInvariantViolationError,
    DagsterDbtError as DagsterDbtError,
)
from .freshness_builder import (
    build_freshness_checks_from_dbt_assets as build_freshness_checks_from_dbt_assets,
)
from .version import __version__ as __version__

# isort: split

# ########################
# ##### DYNAMIC IMPORTS
# ########################
import importlib
from typing import TYPE_CHECKING, Any, Mapping, Sequence, Tuple

from dagster._annotations import deprecated
from dagster._core.libraries import DagsterLibraryRegistry
from dagster._utils.warnings import deprecation_warning
from typing_extensions import Final

DagsterLibraryRegistry.register("dagster-dbt", __version__)

if TYPE_CHECKING:
    ##### EXAMPLE
    # from dagster.some.module import (
    #     Foo as Foo,
    # )

    # isort: split
    ##### Deprecating DbtCliClientResource
    from .core import (
        DbtCliClientResource as DbtCliClientResource,
        DbtCliOutput as DbtCliOutput,
        dbt_cli_resource as dbt_cli_resource,
    )
    from .dbt_resource import DbtResource as DbtResource
    from .errors import (
        DagsterDbtCliFatalRuntimeError as DagsterDbtCliFatalRuntimeError,
        DagsterDbtCliHandledRuntimeError as DagsterDbtCliHandledRuntimeError,
        DagsterDbtCliOutputsNotFoundError as DagsterDbtCliOutputsNotFoundError,
    )
    from .types import DbtOutput as DbtOutput

    ##### Deprecating dbt ops
    # isort: split
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

    ##### Deprecating load_assets_from_XXX
    # isort: split
    from .asset_defs import (
        load_assets_from_dbt_manifest as load_assets_from_dbt_manifest,
        load_assets_from_dbt_project as load_assets_from_dbt_project,
    )

_DEPRECATED: Final[Mapping[str, Tuple[str, str, str]]] = {
    ##### EXAMPLE
    # "Foo": (
    #     "dagster.some.module",
    #     "1.1.0",  # breaking version
    #     "Use Bar instead.",
    # ),
    **{
        value: (
            module,
            "0.24.0",
            additional_warn_text,
        )
        for value, module, additional_warn_text in [
            (
                "DbtCliClientResource",
                "dagster_dbt.core",
                "Use DbtCliResource instead",
            ),
            ("DbtCliOutput", "dagster_dbt.core", None),
            (
                "dbt_cli_resource",
                "dagster_dbt.core",
                "Use DbtCliResource instead",
            ),
            (
                "DbtResource",
                "dagster_dbt.dbt_resource",
                "Use DbtCliResource instead",
            ),
            ("DagsterDbtCliFatalRuntimeError", "dagster_dbt.errors", None),
            ("DagsterDbtCliHandledRuntimeError", "dagster_dbt.errors", None),
            ("DagsterDbtCliOutputsNotFoundError", "dagster_dbt.errors", None),
            ("DbtOutput", "dagster_dbt.types", None),
        ]
    },
    **{
        value: (
            module,
            "0.24.0",
            (
                "Use the @dbt_assets decorator, DbtCliResource, and DagsterDbtTranslator instead.\n\n"
                "For examples on how to use @dbt_assets and DbtCliResource to execute commands like"
                " `dbt run` or `dbt build` on your dbt project, see our API docs:"
                " https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.dbt_assets.\n\n"
                "For examples on how to customize your dbt assets using DagsterDbtTranslator"
                " see the reference:"
                " https://docs.dagster.io/integrations/dbt/reference#understanding-asset-definition-attributes"
                f"{additional_text}"
            ),
        )
        for value, module, additional_text in [
            (
                "load_assets_from_dbt_manifest",
                "dagster_dbt.asset_defs",
                "",
            ),
            (
                "load_assets_from_dbt_project",
                "dagster_dbt.asset_defs",
                (
                    ".\n\nTo generate a dbt manifest for @dbt_assets at run time using `dbt parse`,"
                    " see the reference:"
                    " https://docs.dagster.io/integrations/dbt/reference#loading-dbt-models-from-a-dbt-project"
                ),
            ),
        ]
    },
}

_DEPRECATED_WARNING: Final[Mapping[str, Tuple[str, str, str]]] = {
    ##### EXAMPLE
    # "Foo": (
    #     "dagster.some.module",
    #     "1.1.0",  # breaking version
    #     "Use Bar instead.",
    # ),
    **{
        value: (
            module,
            "0.24.0",
            (
                "Use the @op decorator and DbtCliResource instead.\n\n"
                "For examples on how to use @op and DbtCliResource to execute commands like"
                " `dbt run` or `dbt build`, see our API docs:"
                " https://docs.dagster.io/_apidocs/libraries/dagster-dbt#dagster_dbt.DbtCliResource.cli"
            ),
        )
        for value, module in [
            ("dbt_build_op", "dagster_dbt.ops"),
            ("dbt_compile_op", "dagster_dbt.ops"),
            ("dbt_docs_generate_op", "dagster_dbt.ops"),
            ("dbt_ls_op", "dagster_dbt.ops"),
            ("dbt_run_op", "dagster_dbt.ops"),
            ("dbt_seed_op", "dagster_dbt.ops"),
            ("dbt_snapshot_op", "dagster_dbt.ops"),
            ("dbt_test_op", "dagster_dbt.ops"),
        ]
    },
}


def __getattr__(name: str) -> Any:
    if name in _DEPRECATED:
        module, breaking_version, additional_warn_text = _DEPRECATED[name]

        value = deprecated(
            breaking_version=breaking_version, additional_warn_text=additional_warn_text
        )(getattr(importlib.import_module(module), name))

        return value
    elif name in _DEPRECATED_WARNING:
        module, breaking_version, additional_warn_text = _DEPRECATED_WARNING[name]

        if additional_warn_text:
            deprecation_warning(name, breaking_version, additional_warn_text)

        value = getattr(importlib.import_module(module), name)

        return value
    else:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> Sequence[str]:
    return [*globals(), *_DEPRECATED.keys()]
