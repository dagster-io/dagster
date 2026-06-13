"""Component for executing a dbt project natively on Snowflake.

This component exposes a dbt project that has been deployed to Snowflake as a
``DBT PROJECT`` object (see `dbt Projects on Snowflake
<https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake>`__)
as a set of Dagster assets.

It is modeled on :py:class:`dagster_dbt.DbtCloudComponent`: there is **no local copy of
the dbt project**. Instead, everything is driven through native Snowflake commands:

- The dbt manifest is fetched *from Snowflake*. During state refresh the component runs
  ``EXECUTE DBT PROJECT <name> ARGS='parse'`` to produce the dbt artifacts, locates them
  with ``SYSTEM$LOCATE_DBT_ARTIFACTS(<query_id>)``, and downloads ``manifest.json``. The
  manifest is cached as the component's defs-state (the standard ``StateBackedComponent``
  behavior) -- no dbt artifacts are committed to your repository.
- Execution is remote: ``execute()`` submits ``EXECUTE DBT PROJECT <name> ARGS='...'``
  asynchronously over a :py:class:`dagster_snowflake.SnowflakeResource` connection so the
  dbt run happens inside Snowflake's managed runtime. Dagster polls for completion and, if
  the run is cancelled, spins the Snowflake query down with ``SYSTEM$CANCEL_QUERY``.

Only the manifest -> AssetSpec translation logic from ``dagster-dbt`` is used (it operates
purely on a manifest dictionary); local dbt-core execution is never performed. This
component therefore requires the optional ``dagster-dbt`` dependency::

    pip install 'dagster-snowflake[dbt]'
"""

import glob
import json
import os
import re
import sys
import tempfile
import time
import zipfile
from collections import defaultdict
from collections.abc import Iterator, Mapping
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, TypeAlias

import dagster as dg
from dagster._annotations import preview, public
from dagster._core.definitions.metadata import TableMetadataSet
from dagster._core.definitions.utils import INVALID_NAME_CHARS
from dagster._core.errors import DagsterExecutionInterruptedError
from dagster._time import get_current_timestamp
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.utils.defs_state import DefsStateConfig
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_dbt.asset_utils import (
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
    default_metadata_from_dbt_resource_props,
    get_asset_check_key_for_test,
    get_node,
    get_subset_selection_for_context,
)
from dagster_dbt.cloud_v2.run_handler import (
    COMPLETED_AT_TIMESTAMP_METADATA_KEY,
    get_completed_at_timestamp,
)
from dagster_dbt.compat import REFABLE_NODE_TYPES, NodeStatus, NodeType, TestStatus
from dagster_dbt.components.dbt_component_utils import (
    DagsterDbtComponentTranslatorSettings,
    _set_resolution_context,
    build_op_spec,
    resolve_cli_args,
)
from dagster_dbt.core.dbt_cli_event import EventHistoryMetadata, _build_column_lineage_metadata
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType
from pydantic import Field

from dagster_snowflake.resources import SnowflakeResource

logger = dg.get_dagster_logger()

DbtMetadataAddons: TypeAlias = Literal["column_metadata", "row_count"]

# dbt command used to (re)generate the manifest artifacts inside Snowflake during state
# refresh. `parse` is the lightest command that produces a manifest; `compile` also works.
_DEFAULT_MANIFEST_ARGS: list[str] = ["parse"]

_MANIFEST_FILENAME = "manifest.json"
_RUN_RESULTS_FILENAME = "run_results.json"

# Observation sensor defaults.
_DEFAULT_SENSOR_INTERVAL_SECONDS = 30
_SENSOR_LOOKBACK_SECONDS = 60  # On first tick, only look back this far to avoid backfilling.

# How often (seconds) to poll Snowflake for completion of an async EXECUTE DBT PROJECT run.
_DEFAULT_POLL_INTERVAL_SECONDS = 5

# Marker embedded in the session QUERY_TAG of every Dagster-triggered run. The observation
# sensor uses it to identify (and skip) runs Dagster launched -- a first-class metadata field
# that persists in the query history, unlike a sentinel string smuggled through `ARGS`. It also
# attributes Snowflake credit usage back to the originating Dagster run.
_QUERY_TAG_MARKER = "dagster_dbt_project_component"


def _dagster_query_tag(run_id: str | None) -> str:
    """Return the JSON QUERY_TAG used to mark a Dagster-triggered ``EXECUTE DBT PROJECT`` run."""
    return json.dumps({"app": _QUERY_TAG_MARKER, "dagster_run_id": run_id}, separators=(",", ":"))


class SnowflakeConnectionArgs(dg.Model, dg.Resolvable):
    """Connection arguments for the Snowflake account that hosts the dbt project."""

    account: str = Field(description="Your Snowflake account identifier.")
    user: str = Field(description="Snowflake user login name.")
    password: str | None = Field(default=None, description="Snowflake user password.")
    private_key: str | None = Field(
        default=None,
        description="Raw private key to use for key-pair authentication.",
    )
    private_key_path: str | None = Field(
        default=None,
        description="Path to a private key file to use for key-pair authentication.",
    )
    private_key_password: str | None = Field(
        default=None,
        description="Password for the private key, if it is encrypted.",
    )
    authenticator: str | None = Field(
        default=None,
        description="Authenticator to use (e.g. ``externalbrowser`` or ``oauth``).",
    )
    role: str | None = Field(default=None, description="Snowflake role to use.")
    warehouse: str | None = Field(
        default=None,
        description="Snowflake virtual warehouse used to run the dbt project.",
    )
    database: str | None = Field(default=None, description="Default Snowflake database.")
    schema_: str | None = Field(
        default=None,
        alias="schema",
        description="Default Snowflake schema.",
    )


def resolve_snowflake(context: ResolutionContext, model: Any) -> SnowflakeResource:
    """Resolve a :py:class:`SnowflakeResource` from the component configuration."""
    resolved_val = context.resolve_value(model)
    if isinstance(resolved_val, SnowflakeResource):
        return resolved_val
    args = SnowflakeConnectionArgs.resolve_from_model(context, model)
    return SnowflakeResource(
        account=args.account,
        user=args.user,
        password=args.password,
        private_key=args.private_key,
        private_key_path=args.private_key_path,
        private_key_password=args.private_key_password,
        authenticator=args.authenticator,
        role=args.role,
        warehouse=args.warehouse,
        database=args.database,
        schema=args.schema_,  # ty: ignore[unknown-argument]
    )


def build_execute_dbt_project_sql(project_name: str, args: list[str]) -> str:
    """Build the ``EXECUTE DBT PROJECT`` statement for a deployed Snowflake dbt project.

    Args:
        project_name: The (optionally fully-qualified) name of the ``DBT PROJECT`` object
            in Snowflake, e.g. ``my_db.my_schema.my_project``.
        args: The dbt CLI arguments to pass through, e.g. ``["build", "--select", "tag:x"]``.
    """
    args_str = " ".join(args)
    # Embed the args in a single-quoted Snowflake string literal; escape single quotes
    # by doubling them per the Snowflake string-literal grammar.
    escaped = args_str.replace("'", "''")
    return f"EXECUTE DBT PROJECT {project_name} ARGS='{escaped}'"


def build_dbt_project_execution_history_sql(database: str, schema: str, object_name: str) -> str:
    """Build the ``DBT_PROJECT_EXECUTION_HISTORY`` query for a deployed dbt project object.

    Returns recent runs (query id + completion time) for the project, most-recent last, used by
    the observation sensor to discover dbt runs executed in Snowflake outside of Dagster.
    """
    return (
        "SELECT query_id, query_end_time FROM "
        "TABLE(SNOWFLAKE.INFORMATION_SCHEMA.DBT_PROJECT_EXECUTION_HISTORY("
        f"DATABASE => '{database}', SCHEMA => '{schema}', OBJECT_NAME => '{object_name}')) "
        "ORDER BY query_end_time"
    )


def build_locate_artifacts_sql(query_id: str) -> str:
    """Build the ``SYSTEM$LOCATE_DBT_ARTIFACTS`` call for a dbt run's query id.

    Returns SQL that yields the ``snow://`` stage path containing the run's artifacts
    (including ``results/target/manifest.json`` and ``results/dbt_artifacts.zip``).
    """
    escaped = query_id.replace("'", "''")
    return f"SELECT SYSTEM$LOCATE_DBT_ARTIFACTS('{escaped}')"


def build_get_dbt_log_sql(query_id: str, max_num_lines: int = 10000) -> str:
    """Build the ``SYSTEM$GET_DBT_LOG`` call that returns a run's dbt stdout/log text.

    The dbt log is not part of the ``EXECUTE DBT PROJECT`` result set; it must be fetched
    separately by query id.
    """
    escaped = query_id.replace("'", "''")
    return f"SELECT SYSTEM$GET_DBT_LOG('{escaped}', {max_num_lines})"


def build_set_query_tag_sql(tag: str) -> str:
    """Build the ``ALTER SESSION SET QUERY_TAG`` statement used to mark Dagster-triggered runs."""
    escaped = tag.replace("'", "''")
    return f"ALTER SESSION SET QUERY_TAG = '{escaped}'"


def build_cancel_query_sql(query_id: str) -> str:
    """Build the ``SYSTEM$CANCEL_QUERY`` call used to spin down an orphaned dbt run."""
    escaped = query_id.replace("'", "''")
    return f"SELECT SYSTEM$CANCEL_QUERY('{escaped}')"


def build_dagster_query_ids_sql(marker: str, result_limit: int = 10000) -> str:
    """Build the query that returns the query ids of recent Dagster-triggered runs.

    Looks up the session ``QUERY_TAG`` (set by :py:meth:`SnowflakeDbtProjectComponent.execute`)
    in ``INFORMATION_SCHEMA.QUERY_HISTORY`` so the observation sensor can filter those runs out
    of the execution history -- a robust, first-class alternative to parsing the ``ARGS`` column.
    """
    escaped = marker.replace("'", "''")
    return (
        f"SELECT query_id FROM TABLE(INFORMATION_SCHEMA.QUERY_HISTORY(RESULT_LIMIT => {result_limit})) "
        f"WHERE query_tag LIKE '%{escaped}%'"
    )


def build_show_dbt_artifacts_function_sql() -> str:
    """Build the feature-detection probe used to fail cleanly on unsupported accounts."""
    return "SHOW FUNCTIONS LIKE 'SYSTEM$LOCATE_DBT_ARTIFACTS'"


def _quote_list(values: list[str]) -> str:
    """Render ``values`` as a SQL string-literal list, e.g. ``'A', 'B'``."""
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)


def build_information_schema_tables_sql(database: str, schemas: list[str]) -> str:
    """Build the bulk ``INFORMATION_SCHEMA.TABLES`` query used to fetch model row counts.

    ``ROW_COUNT`` in ``INFORMATION_SCHEMA.TABLES`` is maintained by Snowflake and served from
    cloud services -- no warehouse is required -- so all row counts for a database come back in a
    single lightweight query instead of one ``SELECT count(*)`` per model. It is ``NULL`` for
    views, which is exactly the set we skip.
    """
    return (
        f"SELECT table_schema, table_name, row_count FROM {database}.INFORMATION_SCHEMA.TABLES "
        f"WHERE table_schema IN ({_quote_list(schemas)})"
    )


def build_information_schema_columns_sql(database: str, schemas: list[str]) -> str:
    """Build the bulk ``INFORMATION_SCHEMA.COLUMNS`` query used to fetch column schemas.

    Returns every column (with type, in ordinal order) for the requested schemas in one
    cloud-services query, replacing per-model ``DESCRIBE TABLE`` round-trips.
    """
    return (
        "SELECT table_schema, table_name, column_name, data_type "
        f"FROM {database}.INFORMATION_SCHEMA.COLUMNS "
        f"WHERE table_schema IN ({_quote_list(schemas)}) "
        "ORDER BY ordinal_position"
    )


def _find_file(directory: str, filename: str) -> str | None:
    """Return the path to ``filename`` anywhere under ``directory``, or ``None``."""
    matches = glob.glob(os.path.join(directory, "**", filename), recursive=True)
    return matches[0] if matches else None


def _extract_archives(directory: str) -> None:
    """Extract any ``.zip`` artifact bundles in place.

    Snowflake delivers the full dbt ``target`` directory (including ``compiled/`` SQL) inside
    ``dbt_artifacts.zip`` rather than as loose files, so we unzip before searching for artifacts.
    """
    for zip_path in glob.glob(os.path.join(directory, "**", "*.zip"), recursive=True):
        try:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(os.path.dirname(zip_path))
        except Exception as e:
            logger.warning(f"Could not extract dbt artifact archive {zip_path}: {e}")


def _find_target_dir(download_dir: str, run_results_path: str) -> Path:
    """Locate the dbt ``target`` directory within downloaded artifacts.

    Column lineage reads compiled SQL from ``<target>/compiled/<package>/<path>``, so we anchor
    on the downloaded ``compiled`` directory (whose parent is the target dir). The artifact layout
    under the ``snow://`` path isn't guaranteed to place ``compiled`` next to ``run_results.json``,
    so we search for it and fall back to the ``run_results.json`` directory.
    """
    compiled_dirs = glob.glob(os.path.join(download_dir, "**", "compiled"), recursive=True)
    if compiled_dirs:
        return Path(compiled_dirs[0]).parent
    return Path(run_results_path).parent


def _read_json(path: str) -> Mapping[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _default_op_name(project_name: str) -> str:
    """Derive a valid op name from the (possibly qualified) Snowflake project name."""
    leaf = project_name.split(".")[-1]
    sanitized = re.sub(INVALID_NAME_CHARS, "_", leaf).strip("_")
    return sanitized or "snowflake_dbt_assets"


@public
@preview
@dataclass
class SnowflakeDbtProjectComponent(StateBackedComponent, dg.Resolvable):
    """Expose a dbt project deployed on Snowflake to Dagster as a set of assets.

    This component assumes the dbt project has already been deployed to Snowflake as a
    ``DBT PROJECT`` object (via ``CREATE DBT PROJECT`` / ``snow dbt deploy``). It introspects
    the project entirely through native Snowflake commands -- the dbt manifest is fetched
    from Snowflake rather than from a local copy of the project -- and executes the project
    remotely via ``EXECUTE DBT PROJECT``.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_snowflake.SnowflakeDbtProjectComponent
            attributes:
              snowflake_dbt_project_name: "analytics.dbt.jaffle_shop"
              snowflake:
                account: "{{ env.SNOWFLAKE_ACCOUNT }}"
                user: "{{ env.SNOWFLAKE_USER }}"
                password: "{{ env.SNOWFLAKE_PASSWORD }}"
                role: TRANSFORMER
                warehouse: TRANSFORMING
                database: ANALYTICS
                schema: DBT
              cli_args:
                - build
    """

    snowflake: Annotated[
        SnowflakeResource,
        Resolver(
            fn=resolve_snowflake,
            model_field_type=SnowflakeConnectionArgs.model(),
            description="Connection to the Snowflake account that hosts the dbt project.",
            examples=[
                {
                    "account": "{{ env.SNOWFLAKE_ACCOUNT }}",
                    "user": "{{ env.SNOWFLAKE_USER }}",
                    "password": "{{ env.SNOWFLAKE_PASSWORD }}",
                    "role": "TRANSFORMER",
                    "warehouse": "TRANSFORMING",
                    "database": "ANALYTICS",
                    "schema": "DBT",
                },
            ],
        ),
    ]
    snowflake_dbt_project_name: Annotated[
        str,
        Resolver.default(
            description=(
                "The name of the deployed DBT PROJECT object in Snowflake, optionally "
                "fully-qualified as `database.schema.project`."
            ),
            examples=["analytics.dbt.jaffle_shop"],
        ),
    ]
    cli_args: Annotated[
        list[str | dict[str, Any]],
        Resolver.passthrough(
            description="Arguments to pass to dbt when executing. Defaults to `['build']`.",
            examples=[
                ["run"],
                ["build", "--full-refresh"],
            ],
        ),
    ] = field(default_factory=lambda: ["build"])
    manifest_args: Annotated[
        list[str],
        Resolver.default(
            description=(
                "dbt command used to (re)generate the manifest in Snowflake during state "
                "refresh. Defaults to `['parse']`; use `['compile']` if your project requires it."
            ),
            examples=[["compile"]],
        ),
    ] = field(default_factory=lambda: list(_DEFAULT_MANIFEST_ARGS))
    include_metadata: Annotated[
        list[DbtMetadataAddons],
        Resolver.default(
            description=(
                "Optionally fetch additional metadata for each model after the run by querying "
                "Snowflake's INFORMATION_SCHEMA in bulk: `row_count` attaches "
                "`INFORMATION_SCHEMA.TABLES.ROW_COUNT` per materialized model (views are skipped), "
                "and `column_metadata` attaches the column schema and column-level lineage. These "
                "are served from cloud services (no warehouse), matching the opt-in behavior of "
                "the dbt core component."
            ),
            examples=[
                ["row_count"],
                ["row_count", "column_metadata"],
            ],
        ),
    ] = field(default_factory=list)
    op: Annotated[
        OpSpec | None,
        Resolver.default(
            description="Op related arguments to set on the generated dbt assets.",
            examples=[
                {
                    "name": "some_op",
                    "tags": {"tag1": "value"},
                    "backfill_policy": {"type": "single_run"},
                },
            ],
        ),
    ] = None
    select: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models in the project you want to include.",
            examples=["tag:dagster"],
        ),
    ] = DBT_DEFAULT_SELECT
    exclude: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models in the project you want to exclude.",
            examples=["tag:skip_dagster"],
        ),
    ] = DBT_DEFAULT_EXCLUDE
    selector: Annotated[
        str,
        Resolver.default(
            description="The dbt selector for models in the project you want to include.",
            examples=["custom_selector"],
        ),
    ] = DBT_DEFAULT_SELECTOR
    translation: Annotated[
        TranslationFn[Mapping[str, Any]] | None,
        TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"node": data}),
    ] = None
    translation_settings: Annotated[
        DagsterDbtComponentTranslatorSettings | None,
        Resolver.default(
            description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
            examples=[
                {
                    "enable_source_tests_as_checks": True,
                },
            ],
        ),
    ] = field(default_factory=DagsterDbtComponentTranslatorSettings)
    poll_interval_seconds: Annotated[
        float,
        Resolver.default(
            description=(
                "How often, in seconds, Dagster polls Snowflake for completion of the async "
                "`EXECUTE DBT PROJECT` run."
            ),
        ),
    ] = _DEFAULT_POLL_INTERVAL_SECONDS
    create_sensor: Annotated[
        bool,
        Resolver.default(
            description=(
                "Whether to create a polling sensor that reports materializations for dbt runs "
                "executed in Snowflake outside of Dagster (e.g. via Snowflake Tasks, Snowsight, or "
                "`snow dbt execute`). The sensor polls `DBT_PROJECT_EXECUTION_HISTORY` and emits "
                "materializations from each run's `run_results.json`, analogous to the dbt Cloud "
                "component's external-run sensor."
            ),
        ),
    ] = False

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig(
            key=f"SnowflakeDbtProjectComponent[{self.snowflake_dbt_project_name}]",
            management_type=DefsStateManagementType.LOCAL_FILESYSTEM,
            refresh_if_dev=True,
        )

    @property
    def op_config_schema(self) -> type[dg.Config] | None:
        return None

    @property
    def config_cls(self) -> type[dg.Config] | None:
        return self.op_config_schema

    def _get_op_spec(self) -> OpSpec:
        return build_op_spec(
            op=self.op,
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            op_name=_default_op_name(self.snowflake_dbt_project_name),
        )

    @cached_property
    def _settings(self) -> DagsterDbtComponentTranslatorSettings:
        # There are no local files to reference, so code references are disabled (as in
        # DbtCloudComponent).
        settings = self.translation_settings or DagsterDbtComponentTranslatorSettings()
        return replace(settings, enable_code_references=False)

    @cached_property
    def translator(self) -> "DagsterDbtTranslator":
        return SnowflakeDbtProjectComponentTranslator(self, self._settings)

    @cached_property
    def _base_translator(self) -> "DagsterDbtTranslator":
        return DagsterDbtTranslator(self._settings)

    def get_resource_props(self, manifest: Mapping[str, Any], unique_id: str) -> Mapping[str, Any]:
        """Returns the dictionary of properties for a dbt resource from a parsed manifest.

        This is a convenience method for use when overriding :py:meth:`get_asset_spec`.
        """
        return get_node(manifest, unique_id)

    @public
    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Any
    ) -> dg.AssetSpec:
        """Generates an AssetSpec for a given dbt node.

        Override in a subclass to customize how dbt nodes are converted to Dagster asset
        specs (e.g. to add a ``snowflake`` kind or Snowflake-specific metadata). By default
        it delegates to the configured DagsterDbtTranslator. ``project`` is always ``None``
        (execution and introspection are remote).
        """
        return self._base_translator.get_asset_spec(manifest, unique_id, project)

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        *,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Any,
    ) -> dg.AssetCheckSpec | None:
        return self._base_translator.get_asset_check_spec(asset_spec, manifest, unique_id, project)

    def _download_artifacts(self, cursor: Any, artifact_path: str, dest_dir: str) -> None:
        """Download a dbt run's artifacts from a ``snow://`` stage path to a local dir.

        Isolated so it can be overridden / mocked; uses the Snowflake ``GET`` command.
        """
        cursor.execute(f"GET '{artifact_path}' 'file://{dest_dir}'")

    def _download_run_artifacts(self, cursor: Any, query_id: str, dest_dir: str) -> bool:
        """Locate a run's artifacts via ``SYSTEM$LOCATE_DBT_ARTIFACTS`` and download them.

        Returns ``False`` if the artifacts could not be located.
        """
        cursor.execute(build_locate_artifacts_sql(query_id))
        located = cursor.fetchone()
        if not located or not located[0]:
            return False
        self._download_artifacts(cursor, located[0], dest_dir)
        # Snowflake bundles the dbt target (compiled SQL, run_results.json) into a zip.
        _extract_archives(dest_dir)
        return True

    def _locate_and_read_artifact(
        self, cursor: Any, query_id: str, filename: str
    ) -> Mapping[str, Any] | None:
        """Locate a run's artifacts and read one JSON file, or ``None`` if not found."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            if not self._download_run_artifacts(cursor, query_id, tmp_dir):
                return None
            path = _find_file(tmp_dir, filename)
            return _read_json(path) if path else None

    def _assert_dbt_projects_supported(self, cursor: Any) -> None:
        """Fail cleanly if the account does not support dbt Projects on Snowflake.

        Probes for ``SYSTEM$LOCATE_DBT_ARTIFACTS`` so an unsupported account surfaces an
        actionable error during state refresh rather than an opaque failure mid-run.
        """
        try:
            cursor.execute(build_show_dbt_artifacts_function_sql())
            rows = cursor.fetchall()
        except Exception as e:
            # A failed probe shouldn't be fatal on its own (e.g. limited SHOW privileges); let
            # the subsequent EXECUTE surface the real error.
            logger.warning(f"Could not verify dbt Projects on Snowflake support: {e}")
            return
        if not rows:
            raise dg.DagsterInvariantViolationError(
                "This Snowflake account does not appear to support 'dbt Projects on Snowflake' "
                "(SYSTEM$LOCATE_DBT_ARTIFACTS is unavailable). See "
                "https://docs.snowflake.com/en/user-guide/data-engineering/dbt-projects-on-snowflake."
            )

    def _fetch_manifest(self) -> Mapping[str, Any]:
        """Fetch the dbt manifest natively from Snowflake.

        Runs ``EXECUTE DBT PROJECT ... ARGS='parse'`` to generate the artifacts, locates
        them with ``SYSTEM$LOCATE_DBT_ARTIFACTS``, and downloads ``manifest.json``.
        """
        with self.snowflake.get_connection() as conn:
            cursor = conn.cursor()
            self._assert_dbt_projects_supported(cursor)
            cursor.execute(
                build_execute_dbt_project_sql(
                    self.snowflake_dbt_project_name, list(self.manifest_args)
                )
            )
            query_id = cursor.sfqid
            if not query_id:
                raise dg.DagsterInvariantViolationError(
                    f"EXECUTE DBT PROJECT for '{self.snowflake_dbt_project_name}' did not return a "
                    "query id, so its artifacts cannot be located."
                )
            manifest = self._locate_and_read_artifact(cursor, query_id, _MANIFEST_FILENAME)
            if manifest is None:
                raise dg.DagsterInvariantViolationError(
                    f"Could not locate {_MANIFEST_FILENAME} for dbt project "
                    f"'{self.snowflake_dbt_project_name}' (query id {query_id})."
                )
            return manifest

    def write_state_to_path(self, state_path: Path) -> None:
        manifest = self._fetch_manifest()
        state_path.write_text(json.dumps(manifest), encoding="utf-8")

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        if state_path is None:
            return dg.Definitions()

        manifest = json.loads(state_path.read_text(encoding="utf-8"))
        res_ctx = context.resolution_context

        asset_specs, check_specs = build_dbt_specs(
            translator=validate_translator(self.translator),
            manifest=validate_manifest(manifest),
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            project=None,
            io_manager_key=None,
        )
        op_spec = self._get_op_spec()

        @dg.multi_asset(
            specs=asset_specs,
            check_specs=check_specs,
            # Subsetting is supported: when a subset is launched, a `--select`ed
            # `EXECUTE DBT PROJECT` statement runs only the selected models (see `build_execute_sql`).
            can_subset=True,
            name=op_spec.name,
            op_tags=op_spec.tags,
            backfill_policy=op_spec.backfill_policy,
            pool=op_spec.pool,
            config_schema=self.config_cls.to_fields_dict() if self.config_cls else None,
            allow_arbitrary_check_specs=self.translator.settings.enable_source_tests_as_checks,
        )
        def _fn(context: dg.AssetExecutionContext):
            with _set_resolution_context(res_ctx):
                yield from self.execute(context=context, manifest=manifest)

        sensors = []
        if self.create_sensor:
            sensors.append(self._build_observation_sensor(manifest))

        return dg.Definitions(assets=[_fn], sensors=sensors)

    def get_cli_args(self, context: dg.AssetExecutionContext) -> list[str]:
        return resolve_cli_args(self.cli_args, context)

    def _build_dbt_args(
        self, context: dg.AssetExecutionContext, manifest: Mapping[str, Any]
    ) -> list[str]:
        """Build the dbt CLI args, narrowing the selection when the op is subset.

        Uses dagster-dbt's :py:func:`get_subset_selection_for_context`, so a subsetted launch
        runs a `--select fqn:...`ed statement covering exactly the selected assets / checks --
        the same selection logic as the dbt core and dbt Cloud components.
        """
        verb_args = self.get_cli_args(context)
        selection_args, indirect_selection = get_subset_selection_for_context(
            context=context,
            manifest=manifest,
            select=None if self.select == DBT_DEFAULT_SELECT else self.select,
            exclude=None if self.exclude == DBT_DEFAULT_EXCLUDE else self.exclude,
            selector=None if self.selector == DBT_DEFAULT_SELECTOR else self.selector,
            dagster_dbt_translator=validate_translator(self.translator),
            current_dbt_indirect_selection_env=None,
        )
        args = [*verb_args, *selection_args]
        # `EXECUTE DBT PROJECT` can't take env vars, so translate the indirect-selection
        # override into the equivalent dbt CLI flag.
        if indirect_selection:
            args += ["--indirect-selection", indirect_selection]
        return args

    def build_execute_sql(
        self, context: dg.AssetExecutionContext, manifest: Mapping[str, Any]
    ) -> str:
        """Build the ``EXECUTE DBT PROJECT`` statement that will run for this invocation."""
        return build_execute_dbt_project_sql(
            self.snowflake_dbt_project_name, self._build_dbt_args(context, manifest)
        )

    def _cancel_query(self, conn: Any, query_id: str) -> None:
        """Best-effort ``SYSTEM$CANCEL_QUERY`` so an interrupted run doesn't orphan the dbt run."""
        try:
            conn.cursor().execute(build_cancel_query_sql(query_id))
        except Exception as e:
            logger.warning(f"Failed to cancel Snowflake query {query_id}: {e}")

    def _execute_and_wait(
        self, context: dg.AssetExecutionContext, conn: Any, cursor: Any, sql: str
    ) -> str:
        """Submit the dbt run asynchronously and poll Snowflake until it finishes.

        ``EXECUTE DBT PROJECT`` can run for a long time. Submitting it synchronously would block
        a Dagster worker for the whole run and leave the query orphaned in Snowflake if the
        connection drops or the run is cancelled. Instead we submit with ``execute_async`` and
        poll ``get_query_status_throw_if_error`` (which raises if the dbt run fails). If the
        Dagster step is interrupted while polling, we issue ``SYSTEM$CANCEL_QUERY`` so the
        warehouse resources are spun down, then re-raise.
        """
        # Tag the session so Snowflake credit usage is attributed to this Dagster run and the
        # observation sensor can identify (and skip) runs Dagster itself launched.
        cursor.execute(
            build_set_query_tag_sql(_dagster_query_tag(getattr(context, "run_id", None)))
        )
        cursor.execute_async(sql)
        query_id = cursor.sfqid
        if not query_id:
            raise dg.DagsterInvariantViolationError(
                f"EXECUTE DBT PROJECT for '{self.snowflake_dbt_project_name}' did not return a "
                "query id."
            )
        try:
            while conn.is_still_running(conn.get_query_status_throw_if_error(query_id)):
                time.sleep(self.poll_interval_seconds)
        except DagsterExecutionInterruptedError:
            context.log.warning(
                f"Dagster run interrupted; cancelling Snowflake dbt run (query {query_id})."
            )
            self._cancel_query(conn, query_id)
            raise
        # Bind the async results to the cursor (also re-raises if the query ended in error).
        cursor.get_results_from_sfqid(query_id)
        return query_id

    @public
    def execute(self, context: dg.AssetExecutionContext, manifest: Mapping[str, Any]) -> Iterator:
        """Executes the dbt project on Snowflake via ``EXECUTE DBT PROJECT``.

        The statement is submitted asynchronously and polled to completion (cancelling the
        Snowflake query if the Dagster run is interrupted). After the run completes, the run's
        ``run_results.json`` artifact is downloaded from Snowflake and translated into Dagster
        materializations and asset check results with metadata at parity with the dbt core and
        dbt Cloud components (``unique_id``, ``invocation_id``, ``execution_duration``,
        completed-at timestamp, test status, and the static dbt metadata carried on each
        ``AssetSpec``).

        Override in a subclass to customize execution behavior (e.g. custom logging or
        post-processing of the Snowflake run results).

        .. note::
            When the op is subset, only the selected models are run via a ``--select``ed
            ``EXECUTE DBT PROJECT`` statement. Per-model materializations and metadata are
            emitted from ``run_results.json``.
        """
        sql = self.build_execute_sql(context, manifest)
        context.log.info(f"Executing dbt project on Snowflake:\n{sql}")
        with self.snowflake.get_connection() as conn:
            cursor = conn.cursor()
            query_id = self._execute_and_wait(context, conn, cursor, sql)
            # The dbt stdout isn't in the result set, so fetch it separately and surface it.
            self._log_dbt_output(context, cursor, query_id)

            # Keep the connection (and the downloaded artifacts) open for the duration of
            # event iteration.
            with tempfile.TemporaryDirectory() as tmp_dir:
                located = bool(query_id) and self._download_run_artifacts(cursor, query_id, tmp_dir)
                run_results_path = _find_file(tmp_dir, _RUN_RESULTS_FILENAME) if located else None

                if run_results_path is None:
                    context.log.warning(
                        "Could not locate run_results.json from the Snowflake dbt run; emitting "
                        "materializations without dbt run metadata."
                    )
                    for asset_key in context.selected_asset_keys:
                        yield dg.MaterializeResult(asset_key=asset_key)
                    return

                run_results = _read_json(run_results_path)
                target_path = _find_target_dir(tmp_dir, run_results_path)

                # Prefetch row counts / column schemas in bulk from INFORMATION_SCHEMA (a
                # cloud-services query, no warehouse) instead of issuing per-model queries.
                row_counts: dict[str, int] = {}
                columns_by_relation: dict[str, dict[str, str]] = {}
                if self.include_metadata:
                    relations = self._collect_relations(run_results, manifest)
                    row_counts, columns_by_relation = self._prefetch_metadata(cursor, relations)

                yield from self._run_results_to_events(
                    run_results,
                    manifest,
                    context=context,
                    row_counts=row_counts,
                    columns_by_relation=columns_by_relation,
                    target_path=target_path,
                )

    def _log_dbt_output(
        self, context: dg.AssetExecutionContext, cursor: Any, query_id: str | None
    ) -> None:
        """Fetch the dbt run's log via ``SYSTEM$GET_DBT_LOG`` and write it to stdout.

        The dbt log is not part of the ``EXECUTE DBT PROJECT`` result set. We write it to
        ``sys.stdout`` (rather than the structured logger) so it lands in the run's compute logs,
        mirroring how the dbt Cloud component surfaces ``get_run_logs()``.
        """
        if not query_id:
            return
        try:
            cursor.execute(build_get_dbt_log_sql(query_id))
            row = cursor.fetchone()
        except Exception as e:
            context.log.warning(f"Could not fetch dbt log for query {query_id}: {e}")
            return
        log_text = row[0] if row else None
        if log_text:
            sys.stdout.write(log_text)
            if not log_text.endswith("\n"):
                sys.stdout.write("\n")

    def _run_results_to_events(
        self,
        run_results: Mapping[str, Any],
        manifest: Mapping[str, Any],
        *,
        context: dg.AssetExecutionContext | None = None,
        row_counts: Mapping[str, int] | None = None,
        columns_by_relation: Mapping[str, Mapping[str, str]] | None = None,
        target_path: Path | None = None,
    ) -> Iterator:
        """Translate a dbt ``run_results.json`` into Dagster events with parity metadata.

        Mirrors :py:meth:`dagster_dbt.cloud_v2.run_handler.DbtCloudJobRunResults.to_default_asset_events`
        (minus the dbt Cloud-only run URL), so model materializations and test check results
        carry the same metadata as the dbt core and dbt Cloud components.

        In op execution (``context`` set) this yields :py:class:`MaterializeResult` /
        :py:class:`AssetCheckResult`, and -- when ``include_metadata`` is set -- attaches row
        counts and column schema / lineage from the prefetched INFORMATION_SCHEMA maps. When
        called ad hoc from the observation sensor (``context`` is ``None``) it yields
        :py:class:`AssetMaterialization` / :py:class:`AssetCheckEvaluation`.
        """
        op_mode = context is not None
        translator = validate_translator(self.translator)
        invocation_id = run_results.get("metadata", {}).get("invocation_id")

        for result in run_results.get("results", []):
            unique_id = result["unique_id"]
            dbt_resource_props = manifest["nodes"].get(unique_id)
            if not dbt_resource_props:
                continue

            default_metadata: dict[str, Any] = {
                "unique_id": unique_id,
                "invocation_id": invocation_id,
                "execution_duration": result.get("execution_time"),
            }
            resource_type = dbt_resource_props["resource_type"]
            status = result["status"]
            is_ephemeral = dbt_resource_props["config"]["materialized"] == "ephemeral"

            if (
                resource_type in REFABLE_NODE_TYPES
                and status == NodeStatus.Success
                and not is_ephemeral
            ):
                asset_key = translator.get_asset_spec(manifest, unique_id, None).key
                metadata = {
                    **default_metadata,
                    COMPLETED_AT_TIMESTAMP_METADATA_KEY: dg.MetadataValue.timestamp(
                        get_completed_at_timestamp(result)
                    ),
                }
                # Extra metadata only applies during op execution (the sensor skips it).
                if op_mode:
                    if "row_count" in self.include_metadata and row_counts is not None:
                        metadata.update(
                            self._row_count_metadata(manifest, dbt_resource_props, row_counts)
                        )
                    if (
                        "column_metadata" in self.include_metadata
                        and columns_by_relation is not None
                        and target_path is not None
                    ):
                        metadata.update(
                            self._column_metadata(
                                manifest,
                                dbt_resource_props,
                                translator,
                                target_path,
                                columns_by_relation,
                            )
                        )
                    yield dg.MaterializeResult(asset_key=asset_key, metadata=metadata)
                else:
                    yield dg.AssetMaterialization(asset_key=asset_key, metadata=metadata)
            elif resource_type == NodeType.Test:
                asset_check_key = get_asset_check_key_for_test(
                    manifest=manifest,
                    dagster_dbt_translator=translator,
                    test_unique_id=unique_id,
                    project=None,
                )
                if asset_check_key is None:
                    continue
                if op_mode and asset_check_key not in context.selected_asset_check_keys:
                    continue
                metadata = {
                    **default_metadata,
                    "status": status,
                    COMPLETED_AT_TIMESTAMP_METADATA_KEY: dg.MetadataValue.timestamp(
                        get_completed_at_timestamp(result)
                    ),
                }
                if result.get("failures") is not None:
                    metadata["dagster_dbt/failed_row_count"] = result["failures"]
                severity = (
                    dg.AssetCheckSeverity.WARN
                    if status == TestStatus.Warn
                    else dg.AssetCheckSeverity.ERROR
                )
                if op_mode:
                    yield dg.AssetCheckResult(
                        passed=status == TestStatus.Pass,
                        asset_key=asset_check_key.asset_key,
                        check_name=asset_check_key.name,
                        metadata=metadata,
                        severity=severity,
                    )
                else:
                    yield dg.AssetCheckEvaluation(
                        passed=status == TestStatus.Pass,
                        asset_key=asset_check_key.asset_key,
                        check_name=asset_check_key.name,
                        metadata=metadata,
                        severity=severity,
                    )

    def _qualified_relation(self, relation_name: str) -> str | None:
        """Normalize a dbt ``relation_name`` to an uppercased ``DB.SCHEMA.NAME`` key.

        Strips identifier quoting and fills in the connection's database / schema for partially
        qualified names, so the same key is used when prefetching and when looking up metadata.
        """
        parts = [p.strip().strip('"') for p in relation_name.split(".") if p.strip()]
        if len(parts) == 3:
            database, schema, name = parts
        elif len(parts) == 2:
            database, schema, name = self.snowflake.database, parts[0], parts[1]
        elif len(parts) == 1:
            database, schema, name = self.snowflake.database, self.snowflake.schema_, parts[0]
        else:
            return None
        if not (database and schema and name):
            return None
        return f"{database}.{schema}.{name}".upper()

    def _collect_relations(
        self, run_results: Mapping[str, Any], manifest: Mapping[str, Any]
    ) -> set[str]:
        """Collect the relation names whose metadata should be prefetched after a run.

        Includes every successfully-built materialized model, plus (when column metadata is
        requested) each model's parents -- column-level lineage needs the parents' schemas too.
        """
        relations: set[str] = set()
        want_columns = "column_metadata" in self.include_metadata
        nodes = manifest.get("nodes", {})
        sources = manifest.get("sources", {})
        parent_map = manifest.get("parent_map", {})
        for result in run_results.get("results", []):
            unique_id = result["unique_id"]
            props = nodes.get(unique_id)
            if not props or props.get("resource_type") not in REFABLE_NODE_TYPES:
                continue
            if result.get("status") != NodeStatus.Success:
                continue
            if props.get("config", {}).get("materialized") == "ephemeral":
                continue
            relation = props.get("relation_name")
            if relation:
                relations.add(relation)
            if want_columns:
                for parent_unique_id in parent_map.get(unique_id, []):
                    parent_props = nodes.get(parent_unique_id) or sources.get(parent_unique_id)
                    parent_relation = parent_props.get("relation_name") if parent_props else None
                    if parent_relation:
                        relations.add(parent_relation)
        return relations

    def _prefetch_metadata(
        self, cursor: Any, relations: set[str]
    ) -> tuple[dict[str, int], dict[str, dict[str, str]]]:
        """Bulk-fetch row counts and column schemas for ``relations`` from INFORMATION_SCHEMA.

        Issues at most one ``INFORMATION_SCHEMA.TABLES`` and one ``INFORMATION_SCHEMA.COLUMNS``
        query per database (INFORMATION_SCHEMA is database-scoped), rather than per-model
        ``SELECT count(*)`` / ``DESCRIBE TABLE`` round-trips. Both views are served from cloud
        services, so no warehouse is spun up.

        Returns ``(row_counts, columns_by_relation)`` keyed by the uppercased ``DB.SCHEMA.NAME``
        relation produced by :py:meth:`_qualified_relation`.
        """
        by_db: dict[str, set[tuple[str, str]]] = defaultdict(set)
        for relation in relations:
            qualified = self._qualified_relation(relation)
            if not qualified:
                continue
            database, schema, name = qualified.split(".")
            by_db[database].add((schema, name))

        row_counts: dict[str, int] = {}
        columns_by_relation: dict[str, dict[str, str]] = {}
        want_row = "row_count" in self.include_metadata
        want_columns = "column_metadata" in self.include_metadata

        for database, pairs in by_db.items():
            schemas = sorted({schema for schema, _ in pairs})
            names = {name for _, name in pairs}
            if want_row:
                try:
                    cursor.execute(build_information_schema_tables_sql(database, schemas))
                    for schema, name, row_count in cursor.fetchall():
                        if name.upper() not in names or row_count is None:
                            continue
                        row_counts[f"{database}.{schema}.{name}".upper()] = row_count
                except Exception as e:
                    logger.warning(f"Could not fetch row counts from {database}: {e}")
            if want_columns:
                try:
                    cursor.execute(build_information_schema_columns_sql(database, schemas))
                    for schema, name, column, data_type in cursor.fetchall():
                        if name.upper() not in names:
                            continue
                        key = f"{database}.{schema}.{name}".upper()
                        columns_by_relation.setdefault(key, {})[column] = data_type
                except Exception as e:
                    logger.warning(f"Could not fetch column schemas from {database}: {e}")
        return row_counts, columns_by_relation

    def _row_count_metadata(
        self,
        manifest: Mapping[str, Any],
        dbt_resource_props: Mapping[str, Any],
        row_counts: Mapping[str, int],
    ) -> dict[str, Any]:
        """Attach a model's row count from the prefetched INFORMATION_SCHEMA.TABLES map.

        Views have a ``NULL`` ``ROW_COUNT`` (and so never appear in ``row_counts``), which matches
        the dbt core component's behavior of skipping them.
        """
        if dbt_resource_props["config"]["materialized"] == "view":
            return {}
        relation_name = dbt_resource_props.get("relation_name")
        if not relation_name:
            return {}
        key = self._qualified_relation(relation_name)
        if not key or key not in row_counts:
            return {}
        adapter_type = manifest.get("metadata", {}).get("adapter_type")
        return {**TableMetadataSet(row_count=row_counts[key], storage_kind=adapter_type)}

    def _column_metadata(
        self,
        manifest: Mapping[str, Any],
        dbt_resource_props: Mapping[str, Any],
        translator: DagsterDbtTranslator,
        target_path: Path,
        columns_by_relation: Mapping[str, Mapping[str, str]],
    ) -> dict[str, Any]:
        """Attach column schema + column-level lineage from the prefetched COLUMNS map.

        The warehouse-introspected types (from ``INFORMATION_SCHEMA.COLUMNS``) are merged with
        any dbt-documented column descriptions/tags from the manifest, so the schema carries both
        the authoritative type and the dbt docs. The warehouse columns -- together with the run's
        compiled SQL under ``target_path`` -- are fed into dagster-dbt's
        :py:func:`_build_column_lineage_metadata`, which derives the lineage with sqlglot. Mirrors
        ``_fetch_column_metadata`` in the dbt core event iterator.
        """
        relation_name = dbt_resource_props.get("relation_name")
        if not relation_name:
            return {}
        key = self._qualified_relation(relation_name)
        column_types = columns_by_relation.get(key) if key else None
        if not column_types:
            return {}

        # Merge the warehouse-introspected types with any dbt-documented descriptions/tags.
        documented = {
            name.lower(): info for name, info in (dbt_resource_props.get("columns") or {}).items()
        }
        merged_columns: dict[str, dict[str, Any]] = {}
        for name, data_type in column_types.items():
            doc = documented.get(name.lower(), {})
            entry: dict[str, Any] = {"data_type": data_type}
            if doc.get("description"):
                entry["description"] = doc["description"]
            if doc.get("tags"):
                entry["tags"] = doc["tags"]
            merged_columns[name] = entry
        schema_metadata = default_metadata_from_dbt_resource_props({"columns": merged_columns})

        lineage_metadata: Mapping[str, Any] = {}
        try:
            column_schema_data = {
                name: {"data_type": data_type} for name, data_type in column_types.items()
            }
            parents: dict[str, dict[str, Any]] = {}
            for parent_unique_id in manifest.get("parent_map", {}).get(
                dbt_resource_props["unique_id"], []
            ):
                parent_props = manifest["nodes"].get(parent_unique_id) or manifest.get(
                    "sources", {}
                ).get(parent_unique_id)
                parent_relation = parent_props.get("relation_name") if parent_props else None
                if not parent_relation:
                    continue
                parent_key = self._qualified_relation(parent_relation)
                parent_columns = columns_by_relation.get(parent_key) if parent_key else None
                if parent_columns:
                    parents[parent_relation] = {
                        name: {"data_type": data_type} for name, data_type in parent_columns.items()
                    }

            lineage_metadata = _build_column_lineage_metadata(
                event_history_metadata=EventHistoryMetadata(
                    columns=column_schema_data, parents=parents
                ),
                dbt_resource_props=dict(dbt_resource_props),
                manifest=manifest,
                dagster_dbt_translator=translator,
                target_path=target_path,
            )
        except Exception as e:
            logger.warning(
                f"Could not build column lineage for {dbt_resource_props['unique_id']}: {e}"
            )

        return {**schema_metadata, **lineage_metadata}

    def _parse_project_name(self) -> tuple[str | None, str | None, str]:
        """Resolve the project's (database, schema, object_name) for execution-history queries.

        Accepts a fully-qualified ``database.schema.project`` name, or a bare/partial name,
        falling back to the connection's configured database and schema.
        """
        parts = self.snowflake_dbt_project_name.split(".")
        if len(parts) == 3:
            return parts[0], parts[1], parts[2]
        if len(parts) == 2:
            return self.snowflake.database, parts[0], parts[1]
        return self.snowflake.database, self.snowflake.schema_, parts[0]

    def _fetch_dagster_query_ids(self, cursor: Any) -> set[str]:
        """Return the query ids of recent Dagster-triggered runs (by their session QUERY_TAG)."""
        try:
            cursor.execute(build_dagster_query_ids_sql(_QUERY_TAG_MARKER))
            return {row[0] for row in cursor.fetchall()}
        except Exception as e:
            logger.warning(f"Could not fetch Dagster-tagged query ids: {e}")
            return set()

    def _poll_external_runs(
        self, manifest: Mapping[str, Any], since_timestamp: float | None
    ) -> tuple[list[Any], float | None]:
        """Find dbt runs completed in Snowflake since ``since_timestamp`` and build their events.

        Returns the list of :py:class:`AssetMaterialization` events and the new high-water-mark
        completion timestamp to persist in the sensor cursor.
        """
        database, schema, object_name = self._parse_project_name()
        if not (database and schema and object_name):
            raise dg.DagsterInvariantViolationError(
                "The observation sensor needs a fully-qualified `snowflake_dbt_project_name` "
                "(`database.schema.project`), or a `database`/`schema` set on the Snowflake "
                f"connection. Got `{self.snowflake_dbt_project_name}`."
            )

        events: list[Any] = []
        max_timestamp = since_timestamp
        with self.snowflake.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(build_dbt_project_execution_history_sql(database, schema, object_name))
            history_rows = cursor.fetchall()
            # Skip runs Dagster itself triggered, identified by their session QUERY_TAG -- the
            # robust, first-class analog of dbt Cloud filtering out its adhoc-job runs.
            dagster_query_ids = self._fetch_dagster_query_ids(cursor)
            for query_id, query_end_time in history_rows:
                ts = (
                    query_end_time.timestamp()
                    if hasattr(query_end_time, "timestamp")
                    else float(query_end_time)
                )
                if since_timestamp is not None and ts <= since_timestamp:
                    continue
                if query_id in dagster_query_ids:
                    continue
                run_results = self._locate_and_read_artifact(
                    cursor, query_id, _RUN_RESULTS_FILENAME
                )
                if run_results is None:
                    continue
                events.extend(
                    event
                    for event in self._run_results_to_events(run_results, manifest)
                    if isinstance(event, dg.AssetMaterialization)
                )
                max_timestamp = ts if max_timestamp is None else max(max_timestamp, ts)
        return events, max_timestamp

    def _build_observation_sensor(self, manifest: Mapping[str, Any]) -> dg.SensorDefinition:
        """Build a polling sensor that reports externally-triggered Snowflake dbt runs.

        Analogous to the dbt Cloud component's external-run sensor: it polls
        ``DBT_PROJECT_EXECUTION_HISTORY`` and emits materializations from each new run's
        ``run_results.json``.

        Runs that Dagster itself triggered are skipped: :py:meth:`execute` tags its
        ``EXECUTE DBT PROJECT`` session with a ``QUERY_TAG`` marker, and the sensor filters out
        any history row whose query id carries that tag. So Dagster-materialized and
        externally-triggered runs can safely coexist without double-reporting.
        """
        component = self
        sensor_name = f"{_default_op_name(self.snowflake_dbt_project_name)}__observe_dbt_runs"

        @dg.sensor(
            name=sensor_name,
            minimum_interval_seconds=_DEFAULT_SENSOR_INTERVAL_SECONDS,
            default_status=dg.DefaultSensorStatus.RUNNING,
        )
        def _observe_dbt_runs(context: dg.SensorEvaluationContext) -> dg.SensorResult:
            since_timestamp = (
                float(context.cursor)
                if context.cursor
                else get_current_timestamp() - _SENSOR_LOOKBACK_SECONDS
            )
            events, new_timestamp = component._poll_external_runs(manifest, since_timestamp)  # noqa: SLF001
            if new_timestamp is not None:
                context.update_cursor(str(new_timestamp))
            context.log.info(f"Reporting {len(events)} materialization(s) from external dbt runs.")
            return dg.SensorResult(asset_events=events)

        return _observe_dbt_runs


class SnowflakeDbtProjectComponentTranslator(
    create_component_translator_cls(SnowflakeDbtProjectComponent, DagsterDbtTranslator),  # ty: ignore[unsupported-base]
    ComponentTranslator[SnowflakeDbtProjectComponent],
):
    def __init__(
        self,
        component: SnowflakeDbtProjectComponent,
        settings: DagsterDbtComponentTranslatorSettings | None,
    ):
        self._component = component
        super().__init__(settings)

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Any
    ) -> dg.AssetSpec:
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        if self.component.translation is None:
            return base_spec
        dbt_props = get_node(manifest, unique_id)
        return self.component.translation(base_spec, dbt_props)
