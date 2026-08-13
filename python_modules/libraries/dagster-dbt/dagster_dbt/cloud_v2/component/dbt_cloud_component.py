from collections.abc import Iterator, Mapping
from dataclasses import replace
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypeAlias, cast

import dagster as dg
from dagster import AssetExecutionContext, Definitions, multi_asset
from dagster._annotations import public
from dagster.components import ComponentLoadContext
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.utils.defs_state import DefsStateConfig, DefsStateConfigArgs
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared.serdes import deserialize_value, serialize_value
from pydantic import Field

from dagster_dbt.asset_specs import (
    build_dbt_exposure_asset_specs,
    build_dbt_external_package_asset_specs,
    build_dbt_semantic_layer_asset_specs,
    build_dbt_source_asset_specs,
)
from dagster_dbt.asset_utils import (
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
    get_node,
)
from dagster_dbt.cloud_v2.job_selection import apply_selection
from dagster_dbt.cloud_v2.resources import (
    DAGSTER_ADHOC_PREFIX,
    DbtCloudAdhocJobPoolMode,
    DbtCloudCredentials,
    DbtCloudWorkspace,
)
from dagster_dbt.cloud_v2.sensor_builder import build_dbt_cloud_polling_sensor
from dagster_dbt.cloud_v2.types import DbtCloudJob
from dagster_dbt.components.dbt_component_utils import (
    DagsterDbtComponentTranslatorSettings,
    _set_resolution_context,
    build_op_spec,
    resolve_cli_args,
)
from dagster_dbt.components.dbt_project.component import DbtDeferConfig
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_manifest import validate_manifest

DAGSTER_DBT_CLOUD_JOB_ID_METADATA_KEY = "dagster_dbt/cloud_job_id"
DAGSTER_DBT_CLOUD_JOB_NAME_METADATA_KEY = "dagster_dbt/cloud_job_name"

MirrorJobsMode: TypeAlias = Literal["off", "asset", "job", "both"]


class DbtCloudJobTriggerDefaults(dg.Model, dg.Resolvable):
    """Component-level defaults sent as trigger overrides for every mirrored Cloud job.

    Applies only when ``mirror_jobs`` includes ``"job"`` (i.e. ``"job"`` or ``"both"``).
    Every field is optional — any unset field is not sent to dbt Cloud (the Cloud job's
    configured value is used). Per-run ``DbtCloudJobTriggerConfig`` values (supplied at
    launch time via the Dagster launchpad) override these defaults on a per-field basis.
    """

    cause: str | None = None
    steps_override: list[str] | None = None
    git_sha: str | None = None
    git_branch: str | None = None
    schema_override: str | None = None
    dbt_version_override: str | None = None
    threads_override: int | None = None
    target_name_override: str | None = None
    generate_docs_override: bool | None = None
    timeout_seconds_override: int | None = None


class DbtCloudJobTriggerConfig(dg.Config):
    """Per-run overrides passed to ``trigger_job_run`` when launching a mirrored Cloud job.

    Every field defaults to ``None`` — unset fields are not sent to dbt Cloud, so the
    Cloud job's configured value (or the component-level default from
    ``job_trigger_defaults``) is used. Users see the full override list in the Dagster
    launchpad and can toggle each explicitly.
    """

    cause: str | None = None
    steps_override: list[str] | None = None
    git_sha: str | None = None
    git_branch: str | None = None
    schema_override: str | None = None
    dbt_version_override: str | None = None
    threads_override: int | None = None
    target_name_override: str | None = None
    generate_docs_override: bool | None = None
    timeout_seconds_override: int | None = None


def _build_mirrored_dbt_cloud_job(
    workspace: DbtCloudWorkspace,
    cloud_job: DbtCloudJob,
    trigger_defaults: DbtCloudJobTriggerDefaults | None,
):
    """Return a Dagster ``@job`` that triggers ``cloud_job`` in dbt Cloud and waits.

    Users can schedule this job (``ScheduleDefinition``), monitor it in the Dagster UI,
    and wire ``@run_status_sensor``s to trigger downstream Dagster automation on job
    completion — so treating jobs as first-class Dagster jobs does NOT preclude
    downstream automation. One op wraps ``client.trigger_job_run(job_id)`` +
    ``client.poll_run(run_id)``. On success the run details are attached as op output
    metadata; on failure the op raises with the dbt Cloud run URL and status.

    Trigger overrides (``steps_override``, ``git_sha``, etc.) come from two layers:
    component-level ``trigger_defaults`` merged with per-run ``DbtCloudJobTriggerConfig``
    supplied via Dagster's launchpad. Per-run values win field-by-field.
    """
    from dagster import Failure, MetadataValue, job, op

    cloud_job_id = cloud_job.id
    job_name = cloud_job.sanitized_name()
    defaults_payload = (
        trigger_defaults.model_dump(exclude_none=True) if trigger_defaults is not None else {}
    )

    @op(name=f"{job_name}_trigger")
    def _trigger_op(context, config: DbtCloudJobTriggerConfig):
        client = workspace.get_client()
        # Per-run config wins field-by-field over component-level defaults; any field
        # left unset (None) is not sent to Cloud so the Cloud job's own configured value
        # is used.
        merged = {**defaults_payload, **config.model_dump(exclude_none=True)}
        run_data = client.trigger_job_run(job_id=cloud_job_id, **merged)
        run_id = run_data["id"]
        context.log.info(
            f"Triggered dbt Cloud job {cloud_job_id} run={run_id} overrides={sorted(merged)}"
        )
        final = client.poll_run(run_id=run_id)
        status = final.get("status")
        # dbt Cloud status 10 == success. Fail loudly on anything else so Dagster's
        # normal error surfaces (alerts, retries, run-log context) fire.
        if status != 10:
            raise Failure(
                description=(
                    f"dbt Cloud run {run_id} for job {cloud_job_id} finished with status={status!r}"
                ),
                metadata={
                    "dbt_cloud_run_id": MetadataValue.int(run_id),
                    "dbt_cloud_status": (
                        MetadataValue.int(status)
                        if isinstance(status, int)
                        else MetadataValue.text(str(status))
                    ),
                    "href": MetadataValue.url(final.get("href", "")),
                },
            )
        return {"run_id": run_id, "status": status}

    @job(name=job_name, description=f"Mirrors dbt Cloud job {cloud_job_id} ({cloud_job.name!r}).")
    def _mirrored_job():
        _trigger_op()

    return _mirrored_job


def _iter_mirrorable_cloud_jobs(
    workspace_data: "DbtCloudWorkspaceData",
    include: str | None = None,
    exclude: str | None = None,
) -> Iterator[DbtCloudJob]:
    """Yield user-defined Cloud jobs after selection filtering.

    Filters applied in order:

    1. Drop Dagster's internal adhoc pool jobs (``DAGSTER_ADHOC_JOB__*``) and any ids
       listed in ``workspace_data.adhoc_job_ids``. Implementation detail — never
       user-facing.
    2. Apply the dbt-style selection DSL: ``include`` (default = all) then ``exclude``
       (default = none). See :mod:`dagster_dbt.cloud_v2.job_selection`.
    """
    adhoc_ids = set(workspace_data.adhoc_job_ids)
    candidates: list[DbtCloudJob] = []
    for job_details in workspace_data.jobs:
        if (job_details.get("name") or "").startswith(DAGSTER_ADHOC_PREFIX):
            continue
        if job_details.get("id") in adhoc_ids:
            continue
        candidates.append(DbtCloudJob.from_job_details(job_details))
    yield from apply_selection(candidates, include=include, exclude=exclude)


def _build_dbt_cloud_job_asset_specs(
    workspace_data: "DbtCloudWorkspaceData",
    include: str | None = None,
    exclude: str | None = None,
) -> list["dg.AssetSpec"]:
    """Emit one observable external ``AssetSpec`` per user-defined dbt Cloud job that
    matches the selection filter.

    Job assets participate in Dagster's automation-tick loop: users can attach
    ``AutomationCondition``s to react when a Cloud job runs, schedule the job via
    ``define_asset_job`` + ``ScheduleDefinition``, or key downstream Dagster assets off
    the job's materializations. Kind is ``dbt_cloud_job`` so the UI renders a distinct
    icon.

    Job asset keys are derived from the Cloud job name (sanitized to valid segments) so
    users can reference them stably even if dbt Cloud renames the job.

    Adhoc jobs Dagster created for its own CLI pool are filtered out — they're an
    implementation detail, not user-facing surface area.

    Materialization events for these specs are emitted by the polling sensor when
    ``emit_job_asset_materializations=True`` is passed, so downstream
    ``AutomationCondition``s can react to real Cloud run completions.
    """
    specs: list[dg.AssetSpec] = []
    seen: set[dg.AssetKey] = set()
    for cloud_job in _iter_mirrorable_cloud_jobs(workspace_data, include=include, exclude=exclude):
        key = cloud_job.asset_key()
        if key in seen:
            continue
        seen.add(key)
        specs.append(
            dg.AssetSpec(
                key=key,
                kinds={"dbt_cloud_job"},
                description=f"dbt Cloud job {cloud_job.id}: {cloud_job.name!r}",
                metadata={
                    DAGSTER_DBT_CLOUD_JOB_ID_METADATA_KEY: cloud_job.id,
                    DAGSTER_DBT_CLOUD_JOB_NAME_METADATA_KEY: cloud_job.name or "",
                },
            )
        )
    return specs


if TYPE_CHECKING:
    from dagster_dbt.cloud_v2.types import DbtCloudWorkspaceData


class DbtCloudWorkspaceArgs(dg.Model, dg.Resolvable):
    """Arguments for configuring a dbt Cloud workspace connection from YAML."""

    account_id: int = Field(description="The ID of your dbt Cloud account.")
    token: str = Field(description="Your dbt Cloud API token.")
    access_url: str = Field(
        default="https://cloud.getdbt.com",
        description="Your dbt Cloud workspace URL.",
    )
    project_id: int = Field(description="The ID of the dbt Cloud project.")
    environment_id: int = Field(description="The ID of the dbt Cloud environment.")
    adhoc_job_name: str | None = Field(
        default=None,
        description=(
            "Optional custom name for the ad hoc job created by Dagster. When "
            "`adhoc_job_pool_size > 1`, this value is used as a prefix for the additional "
            "jobs (which receive an `__{index}` suffix)."
        ),
    )
    adhoc_job_pool_size: int = Field(
        default=1,
        ge=1,
        description=(
            "Number of ad hoc dbt Cloud jobs to create. dbt Cloud allows only one concurrent "
            "run per job, so a value greater than 1 lets Dagster run concurrent invocations."
        ),
    )
    adhoc_job_pool_mode: DbtCloudAdhocJobPoolMode = Field(
        default="overflow",
        description=(
            "Behavior when every ad hoc job in the pool already has an active run: "
            "`overflow` triggers on the first job and lets dbt Cloud queue it, `wait` "
            "polls until a job frees up, `fail` raises immediately."
        ),
    )
    request_max_retries: int = Field(
        default=3,
        description="Maximum number of request retries.",
    )
    request_retry_delay: float = Field(
        default=0.25,
        description="Delay between request retries in seconds.",
    )
    request_timeout: int = Field(
        default=15,
        description="Request timeout in seconds.",
    )


def resolve_workspace(context: ResolutionContext, model: Any) -> DbtCloudWorkspace:
    """Resolves the DbtCloudWorkspace from the component configuration."""
    resolved_val = context.resolve_value(model)
    if isinstance(resolved_val, DbtCloudWorkspace):
        return resolved_val
    args = DbtCloudWorkspaceArgs.resolve_from_model(context, model)
    credentials = DbtCloudCredentials(
        account_id=args.account_id,
        token=args.token,
        access_url=args.access_url,
    )
    return DbtCloudWorkspace(
        credentials=credentials,
        project_id=args.project_id,
        environment_id=args.environment_id,
        adhoc_job_name=args.adhoc_job_name,
        adhoc_job_pool_size=args.adhoc_job_pool_size,
        adhoc_job_pool_mode=args.adhoc_job_pool_mode,
        request_max_retries=args.request_max_retries,
        request_retry_delay=args.request_retry_delay,
        request_timeout=args.request_timeout,
    )


@public
class DbtCloudComponent(StateBackedComponent, dg.Resolvable, dg.Model):
    """Expose a dbt Cloud workspace to Dagster as a set of assets."""

    model_config = {"arbitrary_types_allowed": True}

    workspace: Annotated[
        DbtCloudWorkspace,
        Resolver(
            fn=resolve_workspace,
            model_field_type=DbtCloudWorkspaceArgs.model(),
            description="The dbt Cloud workspace resource to use for this component.",
            examples=[
                {
                    "account_id": 123456,
                    "token": "{{ env.DBT_CLOUD_TOKEN }}",
                    "access_url": "https://cloud.getdbt.com",
                    "project_id": 11111,
                    "environment_id": 22222,
                },
            ],
        ),
    ]

    cli_args: Annotated[
        list[str | dict[str, Any]],
        Resolver.passthrough(
            description="Arguments to pass to the dbt CLI when executing. Defaults to `['build']`.",
            examples=[
                ["run"],
                [
                    "build",
                    "--full_refresh",
                    {
                        "--vars": {
                            "start_date": "{{ partition_range_start }}",
                            "end_date": "{{ partition_range_end }}",
                        },
                    },
                ],
            ],
        ),
    ] = Field(default_factory=lambda: ["build"])  # ty: ignore[invalid-assignment]

    op: Annotated[
        OpSpec | None,
        Resolver.default(
            description="Op related arguments to set on the generated @dbt_assets",
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
            description="The dbt selection string for models you want to include.",
            examples=["tag:dagster"],
        ),
    ] = DBT_DEFAULT_SELECT

    exclude: Annotated[
        str,
        Resolver.default(
            description="The dbt selection string for models you want to exclude.",
            examples=["tag:skip_dagster"],
        ),
    ] = DBT_DEFAULT_EXCLUDE

    selector: Annotated[
        str,
        Resolver.default(
            description="The dbt selector for models you want to include.",
            examples=["custom_selector"],
        ),
    ] = DBT_DEFAULT_SELECTOR

    translation: Annotated[
        TranslationFn[Mapping[str, Any]] | None,
        TranslationFnResolver(template_vars_for_translation_fn=lambda data: {"node": data}),
    ] = None

    translation_settings: DagsterDbtComponentTranslatorSettings = Field(
        default_factory=DagsterDbtComponentTranslatorSettings,
        description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
        examples=[
            {
                "enable_source_tests_as_checks": True,
            },
        ],
    )

    create_sensor: Annotated[
        bool,
        Resolver.default(
            description="Whether to create a polling sensor that reports materializations for runs triggered outside of Dagster.",
        ),
    ] = True

    defs_state: Annotated[
        DefsStateConfigArgs,
        Resolver.passthrough(
            description="Configuration for how definitions state should be managed.",
        ),
    ] = Field(default_factory=DefsStateConfigArgs.local_filesystem)

    state_manifest_path: Annotated[
        str | None,
        Resolver.default(
            description=(
                "Optional local path to a `manifest.json` (or a directory containing one) "
                "representing dbt's known-good production state. When set, each dbt model spec "
                "is tagged with `dbt/state=modified|unchanged|new` by comparing per-model "
                "`checksum.checksum` values to the current manifest fetched from dbt Cloud. "
                "Users can then select changed models with `tag:dbt/state=modified` in launch "
                "commands or automation. Only SQL-body changes are detected."
            ),
            examples=["{{ project_root }}/prod_state/manifest.json"],
        ),
    ] = None
    external_packages: Annotated[
        list[str],
        Resolver.default(
            description=(
                "List of dbt package names whose models this project imports as a mesh "
                "dependency. Models in these packages are auto-excluded from the current "
                "project's materializable graph (so `dbt build` doesn't try to rebuild them) "
                "and emitted as observable external stub `AssetSpec`s so downstream lineage "
                "is preserved. When another Dagster code location declares the upstream "
                "project (with the same `AssetKey`s), the auto-stub marker ensures the "
                "upstream's real declaration wins per Dagster's precedence order and the "
                "graph stitches together across code locations."
            ),
            examples=[["silver_project"], ["silver_project", "shared_reference"]],
        ),
    ] = Field(default_factory=list)  # type: ignore
    defer_config: Annotated[
        DbtDeferConfig | None,
        Resolver.default(
            description=(
                "Optional config that appends `--state <path>` (and optionally `--defer` "
                "/ `--favor-state`) to every dbt CLI invocation for this component. Enables "
                "the slim CI / defer-to-prod-state pattern without editing `cli_args` manually."
            ),
            examples=[
                {"state_path": "{{ project_root }}/prod_state"},
                {"state_path": "{{ project_root }}/prod_state", "favor_state": True},
            ],
        ),
    ] = None
    mirror_jobs: Annotated[
        MirrorJobsMode,
        Resolver.default(
            description=(
                "How to surface each dbt Cloud job in Dagster. Defaults to `off` (no "
                "mirroring — backward compatible). Values:\n\n"
                "- `off` — Do not mirror.\n"
                "- `asset` — Emit one observable external `AssetSpec` per Cloud job, "
                "kind `dbt_cloud_job`. The component's polling sensor emits an "
                "`AssetMaterialization` for the job asset whenever a Cloud run for that "
                "job finishes (whether kicked off from dbt Cloud UI, a schedule, or "
                "Dagster). Downstream Dagster assets can react via `AutomationCondition`.\n"
                "- `job` — Emit one Dagster `@job` per Cloud job. Each wraps a single op "
                "that triggers the Cloud job via `trigger_job_run` and polls until "
                "completion. Users schedule via `ScheduleDefinition`, or wire "
                "`@run_status_sensor` to trigger downstream automation when the job "
                "finishes — so this mode is not a dead-end for automation.\n"
                "- `both` — Emit BOTH the asset spec and the Dagster job for each Cloud "
                "job. Users pick which surface they want per use case."
            ),
        ),
    ] = "off"

    job_trigger_defaults: Annotated[
        DbtCloudJobTriggerDefaults | None,
        Resolver.default(
            description=(
                "Component-level defaults sent as trigger overrides for every mirrored "
                "Cloud @job (applies when `mirror_jobs` is `job` or `both`). Any field "
                "left unset is not sent to dbt Cloud, so the Cloud job's configured "
                "value is used. Per-run `DbtCloudJobTriggerConfig` values supplied at "
                "launch time override these defaults on a per-field basis, giving users "
                "explicit control over every override sent to Cloud."
            ),
            examples=[
                {"cause": "Triggered by Dagster", "generate_docs_override": True},
                {"threads_override": 8, "target_name_override": "prod"},
            ],
        ),
    ] = None

    mirror_jobs_select: Annotated[
        str | None,
        Resolver.default(
            description=(
                "dbt-style selection string that limits which Cloud jobs are mirrored. "
                "Space-separated selectors, union (OR) semantics. Supported forms:\n\n"
                "- `type:<value>` — match `job_type` exactly "
                "(`ci`, `merge`, `deploy`, `scheduled`, `other`).\n"
                "- `name:<glob>` — fnmatch glob on the job name (case-sensitive).\n"
                "- `id:<int>` — exact job id match.\n"
                "- `<glob>` — bare token = shorthand for `name:<glob>`.\n\n"
                "Default `None` = mirror every user-defined Cloud job. Applies uniformly "
                "to emitted asset specs (`asset` mode), Dagster jobs (`job` mode), and "
                "the polling sensor — so the sensor never emits materializations for "
                "jobs the user chose not to mirror."
            ),
            examples=["type:deploy", "type:deploy type:merge", "name:Prod_*"],
        ),
    ] = None

    mirror_jobs_exclude: Annotated[
        str | None,
        Resolver.default(
            description=(
                "dbt-style selection string that excludes matching Cloud jobs from "
                "mirroring. Applied AFTER `mirror_jobs_select`; exclusion wins. Same "
                "syntax as `mirror_jobs_select`."
            ),
            examples=["type:ci", "name:*_staging"],
        ),
    ] = None

    monitor_runs: Annotated[
        bool,
        Resolver.default(
            description=(
                "When True, emit AssetMaterializations / AssetCheckResults for each dbt "
                "model / test as it completes mid-run — instead of waiting for the whole "
                "Cloud run to finish. The component polls step debug logs "
                "(`GET /steps/{id}/?include_related=debug_logs`) every `poll_interval` "
                "seconds and parses per-model OK/ERROR status. Downstream `AutomationCondition` "
                "subscriptions can react in seconds instead of minutes. Default `False` "
                "preserves the OOTB wait-for-completion behavior for existing users."
            ),
        ),
    ] = False

    fail_fast: Annotated[
        bool,
        Resolver.default(
            description=(
                "When `monitor_runs=True`: on the first model/test failure, cancel the "
                "Cloud run via `POST /runs/{id}/cancel/` and raise `Failure` after "
                "yielding any partials. Default `False` keeps the run going so all "
                "failures are captured (matches dbt's own `--fail-fast` off default)."
            ),
        ),
    ] = False

    poll_interval: Annotated[
        int,
        Resolver.default(
            description=(
                "Seconds between debug-log polls when `monitor_runs=True`. Default 5. "
                "Lower = faster reaction to model completions but more API calls. dbt "
                "Cloud rate-limits debug-log requests, so don't drop below 2."
            ),
        ),
    ] = 5

    @property
    def defs_state_config(self) -> DefsStateConfig:
        key = f"DbtCloudComponent[{self.workspace.unique_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=key)

    @cached_property
    def _base_translator(self) -> DagsterDbtTranslator:
        settings = replace(self.translation_settings, enable_code_references=False)
        return DagsterDbtTranslator(settings)

    @public
    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Any
    ) -> dg.AssetSpec:
        """Generates an AssetSpec for a given dbt node.

        This method can be overridden in a subclass to customize how dbt nodes are converted
        to Dagster asset specs. By default, it delegates to the configured DagsterDbtTranslator.

        Args:
            manifest: The dbt manifest dictionary containing information about all dbt nodes.
            unique_id: The unique identifier for the dbt node (e.g., "model.my_project.my_model").
            project: Always ``None`` for dbt Cloud (execution is remote).

        Returns:
            An AssetSpec that represents the dbt node as a Dagster asset.

        Example:
            .. code-block:: python

                from dagster_dbt import DbtCloudComponent
                import dagster as dg

                class MyDbtCloudComponent(DbtCloudComponent):
                    def get_asset_spec(self, manifest, unique_id, project):
                        base_spec = super().get_asset_spec(manifest, unique_id, project)
                        return base_spec.replace_attributes(
                            tags={**base_spec.tags, "custom_tag": "my_value"}
                        )
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

    @cached_property
    def translator(self) -> DagsterDbtTranslator:
        settings = replace(self.translation_settings, enable_code_references=False)
        return DbtCloudComponentTranslator(self, settings)

    @property
    def op_config_schema(self) -> type[dg.Config] | None:
        return None

    @property
    def config_cls(self) -> type[dg.Config] | None:
        return self.op_config_schema

    def _get_op_spec(self, op_name: str = "dbt_cloud_assets") -> OpSpec:
        return build_op_spec(
            op=self.op,
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            op_name=op_name,
        )

    def get_cli_args(self, context: AssetExecutionContext) -> list[str]:
        args = resolve_cli_args(self.cli_args, context)
        if self.defer_config is not None:
            args.extend(self.defer_config.to_cli_args())
        return args

    def write_state_to_path(self, state_path: Path) -> None:
        workspace_data = self.workspace.fetch_workspace_data()
        state_path.write_text(serialize_value(workspace_data), encoding="utf-8")

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Path | None
    ) -> Definitions:
        if state_path is None:
            return Definitions()

        workspace_data = cast("DbtCloudWorkspaceData", deserialize_value(state_path.read_text()))
        manifest = workspace_data.manifest
        res_ctx = context.resolution_context

        validated_manifest_for_state = validate_manifest(manifest)
        # External mesh packages: auto-exclude their models from the materializable graph.
        effective_exclude = self.exclude or ""
        if self.external_packages:
            package_exclusions = " ".join(f"package:{pkg}" for pkg in self.external_packages)
            effective_exclude = (
                f"{effective_exclude} {package_exclusions}".strip()
                if effective_exclude
                else package_exclusions
            )
        asset_specs, check_specs = build_dbt_specs(
            translator=self.translator,
            manifest=validated_manifest_for_state,
            select=self.select,
            exclude=effective_exclude,
            selector=self.selector,
            project=None,
            io_manager_key=None,
        )
        # State-aware tagging: same wiring as DbtProjectComponent.
        if self.state_manifest_path:
            from dagster_dbt.components.dbt_project.component import _apply_dbt_state_tags

            asset_specs = _apply_dbt_state_tags(
                asset_specs=asset_specs,
                current_manifest=validated_manifest_for_state,
                state_manifest_path=Path(self.state_manifest_path),
            )

        op_spec = self._get_op_spec("dbt_cloud_assets")

        @multi_asset(
            specs=asset_specs,
            check_specs=check_specs,
            can_subset=True,
            name=op_spec.name,
            op_tags=op_spec.tags,
            backfill_policy=op_spec.backfill_policy,
            pool=op_spec.pool,
            config_schema=self.config_cls.to_fields_dict() if self.config_cls else None,
            allow_arbitrary_check_specs=self.translator.settings.enable_source_tests_as_checks,
        )
        def _dbt_cloud_assets(context: AssetExecutionContext) -> Iterator:
            with _set_resolution_context(res_ctx):
                yield from self.execute(context=context)

        sensors = []
        # When mirroring jobs as assets, the sensor emits an AssetMaterialization for
        # each job asset when its Cloud run finishes, so downstream AutomationConditions
        # can react regardless of who triggered the run (Dagster, dbt Cloud UI, schedule).
        emit_job_materializations = self.mirror_jobs in ("asset", "both")
        if self.create_sensor:
            sensors.append(
                build_dbt_cloud_polling_sensor(
                    workspace=self.workspace,
                    dagster_dbt_translator=self.translator,
                    emit_job_asset_materializations=emit_job_materializations,
                    mirror_jobs_select=self.mirror_jobs_select,
                    mirror_jobs_exclude=self.mirror_jobs_exclude,
                )
            )

        # Mirror DbtProjectComponent: emit dbt sources as observable external AssetSpecs
        # so freshness policies, table metadata, kinds, etc. flow into the graph. dbt Cloud
        # has no local DbtProject object, so pass project=None (code references derived
        # from local file paths aren't meaningful for Cloud-loaded manifests anyway).
        validated_manifest = validate_manifest(manifest)
        source_specs = (
            build_dbt_source_asset_specs(
                manifest=validated_manifest,
                dagster_dbt_translator=self.translator,
                project=None,
            )
            if self.translator.settings.enable_source_assets
            else []
        )
        # Emit dbt exposures (dashboards, notebooks, etc.) as downstream observable specs
        # so users can trace materialization -> consumption chains through the graph.
        exposure_specs = (
            build_dbt_exposure_asset_specs(
                manifest=validated_manifest,
                dagster_dbt_translator=self.translator,
                project=None,
            )
            if self.translator.settings.enable_exposure_assets
            else []
        )
        semantic_layer_specs = (
            build_dbt_semantic_layer_asset_specs(
                manifest=validated_manifest,
                dagster_dbt_translator=self.translator,
                project=None,
            )
            if self.translator.settings.enable_semantic_layer_assets
            else []
        )
        external_package_specs = build_dbt_external_package_asset_specs(
            manifest=validated_manifest,
            external_packages=self.external_packages,
            dagster_dbt_translator=self.translator,
            project=None,
        )

        # dbt Cloud jobs surfaced per `mirror_jobs` mode. Assets and jobs can be emitted
        # independently or together; see the field docstring for use-case guidance.
        emit_asset_specs = self.mirror_jobs in ("asset", "both")
        emit_jobs = self.mirror_jobs in ("job", "both")
        job_specs = (
            _build_dbt_cloud_job_asset_specs(
                workspace_data,
                include=self.mirror_jobs_select,
                exclude=self.mirror_jobs_exclude,
            )
            if emit_asset_specs
            else []
        )
        mirrored_jobs = (
            [
                _build_mirrored_dbt_cloud_job(self.workspace, cloud_job, self.job_trigger_defaults)
                for cloud_job in _iter_mirrorable_cloud_jobs(
                    workspace_data,
                    include=self.mirror_jobs_select,
                    exclude=self.mirror_jobs_exclude,
                )
            ]
            if emit_jobs
            else []
        )

        return Definitions(
            assets=[
                _dbt_cloud_assets,
                *source_specs,
                *exposure_specs,
                *semantic_layer_specs,
                *external_package_specs,
                *job_specs,
            ],
            sensors=sensors,
            jobs=mirrored_jobs,
        )

    def execute(self, context: AssetExecutionContext) -> Iterator:
        invocation = self.workspace.cli(
            args=self.get_cli_args(context),
            dagster_dbt_translator=self.translator,
            context=context,
        )
        yield from invocation.wait(
            monitor_runs=self.monitor_runs,
            fail_fast=self.fail_fast,
            poll_interval=self.poll_interval,
        )


class DbtCloudComponentTranslator(
    create_component_translator_cls(DbtCloudComponent, DagsterDbtTranslator),  # ty: ignore[unsupported-base]
    ComponentTranslator[DbtCloudComponent],
):
    """Translator for :py:class:`DbtCloudComponent` that applies the optional ``translation``
    function from the component's YAML configuration on top of the base
    :py:class:`DagsterDbtTranslator` output.

    Subclasses of :py:class:`DbtCloudComponent` that override ``get_asset_spec`` are
    automatically detected and called before the YAML ``translation`` layer is applied.
    """

    def __init__(
        self,
        component: DbtCloudComponent,
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
