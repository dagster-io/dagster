from collections.abc import Iterator
from dataclasses import replace
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Any, cast

import dagster as dg
from dagster import AssetExecutionContext, Definitions, multi_asset
from dagster._annotations import public
from dagster.components import ComponentLoadContext
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.utils.defs_state import DefsStateConfig, DefsStateConfigArgs
from dagster_shared.serdes import deserialize_value, serialize_value
from pydantic import Field

from dagster_dbt.asset_utils import (
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
)
from dagster_dbt.cloud_v2.resources import DbtCloudCredentials, DbtCloudWorkspace
from dagster_dbt.cloud_v2.sensor_builder import build_dbt_cloud_polling_sensor
from dagster_dbt.components.dbt_component_utils import (
    DagsterDbtComponentTranslatorSettings,
    _set_resolution_context,
    build_op_spec,
    resolve_cli_args,
)
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_manifest import validate_manifest

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
        description="Optional custom name for the ad hoc job created by Dagster.",
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
    ] = Field(default_factory=lambda: ["build"])

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

    @property
    def defs_state_config(self) -> DefsStateConfig:
        key = f"DbtCloudComponent[{self.workspace.unique_id}]"
        return DefsStateConfig.from_args(self.defs_state, default_key=key)

    @cached_property
    def translator(self) -> DagsterDbtTranslator:
        settings = replace(self.translation_settings, enable_code_references=False)
        return DagsterDbtTranslator(settings)

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
        return resolve_cli_args(self.cli_args, context)

    def write_state_to_path(self, state_path: Path) -> None:
        workspace_data = self.workspace.fetch_workspace_data()
        state_path.write_text(serialize_value(workspace_data))

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Path | None
    ) -> Definitions:
        if state_path is None:
            return Definitions()

        workspace_data = cast("DbtCloudWorkspaceData", deserialize_value(state_path.read_text()))
        manifest = workspace_data.manifest
        res_ctx = context.resolution_context

        asset_specs, check_specs = build_dbt_specs(
            translator=self.translator,
            manifest=validate_manifest(manifest),
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            project=None,
            io_manager_key=None,
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
        if self.create_sensor:
            sensors.append(
                build_dbt_cloud_polling_sensor(
                    workspace=self.workspace,
                    dagster_dbt_translator=self.translator,
                )
            )

        return Definitions(assets=[_dbt_cloud_assets], sensors=sensors)

    def execute(self, context: AssetExecutionContext) -> Iterator:
        invocation = self.workspace.cli(
            args=self.get_cli_args(context),
            dagster_dbt_translator=self.translator,
            context=context,
        )
        yield from invocation.wait()
