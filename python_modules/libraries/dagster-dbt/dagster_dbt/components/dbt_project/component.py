from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, TypeAlias

import dagster as dg
from dagster._annotations import public
from dagster._utils.cached_method import cached_method
from dagster.components.component.state_backed_component import StateBackedComponent
from dagster.components.core.component_tree import ComponentTree
from dagster.components.resolved.core_models import OpSpec, ResolutionContext
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.defs_state import DefsStateConfig
from dagster.components.utils.translation import (
    ComponentTranslator,
    TranslationFn,
    TranslationFnResolver,
    create_component_translator_cls,
)
from dagster_shared.serdes.objects.models.defs_state_info import DefsStateManagementType

from dagster_dbt.asset_specs import (
    build_dbt_exposure_asset_specs,
    build_dbt_external_package_asset_specs,
    build_dbt_semantic_layer_asset_specs,
    build_dbt_source_asset_specs,
)
from dagster_dbt.asset_utils import (
    DAGSTER_DBT_STATE_TAG_KEY,
    DAGSTER_DBT_TRANSLATOR_METADATA_KEY,
    DAGSTER_DBT_UNIQUE_ID_METADATA_KEY,
    DBT_DEFAULT_EXCLUDE,
    DBT_DEFAULT_SELECT,
    DBT_DEFAULT_SELECTOR,
    build_dbt_specs,
    compute_dbt_state_tags,
    get_node,
)
from dagster_dbt.components.dbt_component_utils import (
    DagsterDbtComponentTranslatorSettings,
    _set_resolution_context,
    build_op_spec,
    resolve_cli_args,
)
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.dbt_event_iterator import DbtDagsterEventType, DbtEventIterator
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_translator
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject
from dagster_dbt.dbt_project_manager import (
    DbtProjectArgsManager,
    DbtProjectManager,
    NoopDbtProjectManager,
    RemoteGitDbtProjectManager,
)
from dagster_dbt.utils import ASSET_RESOURCE_TYPES


@dataclass
class DbtProjectArgs(dg.Resolvable):
    """Aligns with DbtProject.__new__."""

    project_dir: str
    target_path: str | None = None
    profiles_dir: str | None = None
    profile: str | None = None
    target: str | None = None
    packaged_project_dir: str | None = None
    state_path: str | None = None
    prepare_project_cli_args: list[str] | None = None


def resolve_dbt_project(context: ResolutionContext, model) -> DbtProjectManager:
    if isinstance(model, RemoteGitDbtProjectManager.model()):
        return RemoteGitDbtProjectManager.resolve_from_model(context, model)

    args = (
        DbtProjectArgs(project_dir=context.resolve_value(model, as_type=str))
        if isinstance(model, str)
        else DbtProjectArgs.resolve_from_model(context, model)
    )
    # resolve the project_dir relative to where this component is defined
    args = replace(args, project_dir=context.resolve_source_relative_path(args.project_dir))
    return DbtProjectArgsManager(args)


DbtMetadataAddons: TypeAlias = Literal["column_metadata", "row_count", "insights"]


@public
@dataclass
class DbtDeferConfig(dg.Resolvable):
    """Configuration for dbt's ``--defer``/``--state``/``--favor-state`` runtime options.

    Slim CI pattern: dbt runs models that changed vs a state manifest, deferring ``ref()``
    resolution to the state's tables for unchanged upstream models. Skips rebuilding data
    that hasn't changed.

    Also usable directly from ``@dbt_assets`` — construct one and call ``to_cli_args()``
    to get the flag list to append to your dbt invocation:

    .. code-block:: python

        from dagster_dbt import DbtDeferConfig, DbtCliResource, dbt_assets

        defer = DbtDeferConfig(state_path="/prod/state")

        @dbt_assets(manifest=...)
        def my_assets(context, dbt: DbtCliResource):
            yield from dbt.cli(["build", *defer.to_cli_args()], context=context).stream()

    Args:
        state_path: Path to the state directory (containing ``manifest.json``) or the
            ``manifest.json`` file itself. Passed to dbt via ``--state <path>``.
        defer: If True (default), pass ``--defer`` so missing / unbuilt models resolve
            to the state's tables. Slim CI's core primitive.
        favor_state: If True, pass ``--favor-state`` so dbt prefers the state's version
            even when the current run has updated the table. Useful for cross-environment
            reads. Defaults to False.
    """

    state_path: str
    defer: bool = True
    favor_state: bool = False

    def to_cli_args(self) -> list[str]:
        args: list[str] = ["--state", self.state_path]
        if self.defer:
            args.append("--defer")
        if self.favor_state:
            args.append("--favor-state")
        return args


def _resolve_state_manifest_path(path: Path) -> Path:
    """Accept either a directory containing ``manifest.json`` or a direct file path."""
    if path.is_dir():
        return path / "manifest.json"
    return path


@public
def apply_dbt_state_tags(
    *,
    asset_specs: Sequence["dg.AssetSpec"],
    current_manifest: Mapping[str, Any],
    state_manifest_path: Path,
) -> list["dg.AssetSpec"]:
    """Load a state manifest and attach ``dbt/state=modified|unchanged|new`` tags to
    the supplied asset specs, comparing per-model checksums against ``current_manifest``.

    Useful directly from ``@dbt_assets`` for slim CI + state-aware selection:

    .. code-block:: python

        from dagster_dbt import apply_dbt_state_tags, build_dbt_asset_specs, dbt_assets

        specs = build_dbt_asset_specs(manifest=current_manifest)
        specs = apply_dbt_state_tags(
            asset_specs=specs,
            current_manifest=current_manifest,
            state_manifest_path=Path("/prod/state/manifest.json"),
        )
        # Now specs carry `dbt/state=modified|unchanged|new` — use with dg.AssetSelection
        # to build a "changed models only" job.

    Args:
        asset_specs: The current-manifest specs to tag.
        current_manifest: The current run's dbt manifest.
        state_manifest_path: Path to the state ``manifest.json`` (file or containing dir).

    Returns:
        A new list of tagged specs. Input specs are not mutated.
    """
    import json

    resolved = _resolve_state_manifest_path(state_manifest_path)
    if not resolved.exists():
        raise dg.DagsterInvalidDefinitionError(
            f"state_manifest_path does not exist: {state_manifest_path}. "
            "Provide a path to a manifest.json (or a directory containing one) that "
            "reflects your production dbt project state."
        )
    state_manifest = json.loads(resolved.read_text())
    state_tags_by_unique_id = compute_dbt_state_tags(
        current_manifest=current_manifest, state_manifest=state_manifest
    )

    tagged_specs: list[dg.AssetSpec] = []
    for spec in asset_specs:
        unique_id_meta = spec.metadata.get(DAGSTER_DBT_UNIQUE_ID_METADATA_KEY)
        unique_id = getattr(unique_id_meta, "value", unique_id_meta)
        state = state_tags_by_unique_id.get(str(unique_id or ""))
        tagged_specs.append(
            spec.merge_attributes(tags={DAGSTER_DBT_STATE_TAG_KEY: state}) if state else spec
        )
    return tagged_specs


@public
@scaffold_with(DbtProjectComponentScaffolder)
@dataclass
class DbtProjectComponent(StateBackedComponent, dg.Resolvable):
    """Expose a DBT project to Dagster as a set of assets.

    This component assumes that you have already set up a dbt project, for example, the dbt `Jaffle shop <https://github.com/dbt-labs/jaffle-shop>`_. Run `git clone --depth=1 https://github.com/dbt-labs/jaffle-shop.git jaffle_shop && rm -rf jaffle_shop/.git` to copy that project
    into your Dagster project directory.

    Scaffold a DbtProjectComponent definition by running `dg scaffold defs dagster_dbt.DbtProjectComponent --project-path path/to/your/existing/dbt_project`
    in the Dagster project directory.

    Example:

        .. code-block:: yaml

            # defs.yaml

            type: dagster_dbt.DbtProjectComponent
            attributes:
              project: "{{ project_root }}/path/to/dbt_project"
              cli_args:
                - build
    """

    project: Annotated[
        DbtProject | DbtProjectManager,
        Resolver(
            resolve_dbt_project,
            model_field_type=str | DbtProjectArgs.model() | RemoteGitDbtProjectManager.model(),
            description="The path to the dbt project or a mapping defining a DbtProject",
            examples=[
                "{{ project_root }}/path/to/dbt_project",
                {
                    "project_dir": "path/to/dbt_project",
                    "profile": "your_profile",
                    "target": "your_target",
                },
                {
                    "project_dir": "path/to/dbt_project",
                    "prepare_project_cli_args": ["compile", "--quiet"],
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
    ] = field(default_factory=lambda: ["build"])
    include_metadata: Annotated[
        list[DbtMetadataAddons],
        Resolver.default(
            description="Optionally include additional metadata in materializations generated while executing your dbt models",
            examples=[
                ["row_count"],
                ["row_count", "column_metadata"],
            ],
        ),
    ] = field(default_factory=list)
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
    prepare_if_dev: Annotated[
        bool,
        Resolver.default(
            description="Whether to prepare the dbt project every time in `dagster dev` or `dg` cli calls."
        ),
    ] = True
    state_manifest_path: Annotated[
        str | None,
        Resolver.default(
            description=(
                "Optional local path to a `manifest.json` (or a directory containing one) "
                "representing dbt's known-good production state. When set, each dbt model spec "
                "is tagged with `dbt/state=modified|unchanged|new` by comparing per-model "
                "`checksum.checksum` values to the current manifest. Users can select changed "
                "models with `tag:dbt/state=modified` in launch commands or automation. Only "
                "SQL-body changes are detected (per `state:modified.sql` in dbt); full "
                "`state:modified` semantics (config, macros, contract, etc.) require running "
                "`dbt ls --state <path> --select state:modified` at CI time."
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
    ] = field(default_factory=list)
    defer_config: Annotated[
        DbtDeferConfig | None,
        Resolver.default(
            description=(
                "Optional config that appends `--state <path>` (and optionally `--defer` "
                "/ `--favor-state`) to every dbt CLI invocation for this component. Enables "
                "the slim CI / defer-to-prod-state pattern without requiring users to edit "
                "`cli_args` manually. Users still control the state path — Dagster does not "
                "generate one. Composes with `state_manifest_path` (which is used at defs-load "
                "time for `dbt/state` tagging); pointing both at the same manifest is the "
                "common case."
            ),
            examples=[
                {"state_path": "{{ project_root }}/prod_state"},
                {"state_path": "{{ project_root }}/prod_state", "favor_state": True},
                {"state_path": "{{ project_root }}/prod_state", "defer": False},
            ],
        ),
    ] = None

    @property
    def defs_state_config(self) -> DefsStateConfig:
        return DefsStateConfig(
            key=f"DbtProjectComponent[{self._project_manager.defs_state_discriminator}]",
            management_type=DefsStateManagementType.LOCAL_FILESYSTEM,
            refresh_if_dev=self.prepare_if_dev,
        )

    @property
    def op_config_schema(self) -> type[dg.Config] | None:
        return None

    @property
    def config_cls(self) -> type[dg.Config] | None:
        """Internal property that returns the config schema for the op.

        Delegates to op_config_schema for backwards compatibility and consistency
        with other component types.
        """
        return self.op_config_schema

    def _get_op_spec(self, project: DbtProject) -> OpSpec:
        return build_op_spec(
            op=self.op,
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            op_name=project.name,
        )

    @cached_property
    def translator(self) -> "DagsterDbtTranslator":
        return DbtProjectComponentTranslator(self, self.translation_settings)

    @cached_property
    def _base_translator(self) -> "DagsterDbtTranslator":
        return DagsterDbtTranslator(self.translation_settings)

    def get_resource_props(self, manifest: Mapping[str, Any], unique_id: str) -> Mapping[str, Any]:
        """Given a parsed manifest and a dbt unique_id, returns the dictionary of properties
        for the corresponding dbt resource (e.g. model, seed, snapshot, source) as defined
        in your dbt project. This can be used as a convenience method when overriding the
        `get_asset_spec` method.

        Args:
            manifest (Mapping[str, Any]): The parsed manifest of the dbt project.
            unique_id (str): The unique_id of the dbt resource.

        Returns:
            Mapping[str, Any]: The dictionary of properties for the corresponding dbt resource.

        Examples:
            .. code-block:: python

                class CustomDbtProjectComponent(DbtProjectComponent):

                    def get_asset_spec(self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject]) -> dg.AssetSpec:
                        base_spec = super().get_asset_spec(manifest, unique_id, project)
                        resource_props = self.get_resource_props(manifest, unique_id)
                        if resource_props["meta"].get("use_custom_group"):
                            return base_spec.replace_attributes(group_name="custom_group")
                        else:
                            return base_spec
        """
        return get_node(manifest, unique_id)

    @public
    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: DbtProject | None
    ) -> dg.AssetSpec:
        """Generates an AssetSpec for a given dbt node.

        This method can be overridden in a subclass to customize how dbt nodes are converted
        to Dagster asset specs. By default, it delegates to the configured DagsterDbtTranslator.

        Args:
            manifest: The dbt manifest dictionary containing information about all dbt nodes
            unique_id: The unique identifier for the dbt node (e.g., "model.my_project.my_model")
            project: The DbtProject object, if available

        Returns:
            An AssetSpec that represents the dbt node as a Dagster asset

        Example:
            Override this method to add custom tags to all dbt models:

            .. code-block:: python

                from dagster_dbt import DbtProjectComponent
                import dagster as dg

                class CustomDbtProjectComponent(DbtProjectComponent):
                    def get_asset_spec(self, manifest, unique_id, project):
                        base_spec = super().get_asset_spec(manifest, unique_id, project)
                        return base_spec.replace_attributes(
                            tags={**base_spec.tags, "custom_tag": "my_value"}
                        )
        """
        return DagsterDbtTranslator.get_asset_spec(self.translator, manifest, unique_id, project)

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"],
    ) -> dg.AssetCheckSpec | None:
        return self._base_translator.get_asset_check_spec(asset_spec, manifest, unique_id, project)

    @cached_property
    def _project_manager(self) -> DbtProjectManager:
        if isinstance(self.project, DbtProject):
            return NoopDbtProjectManager(self.project)
        else:
            return self.project

    @cached_property
    def dbt_project(self) -> DbtProject:
        return self._project_manager.get_project(None)

    def get_asset_selection(
        self, select: str, exclude: str = DBT_DEFAULT_EXCLUDE
    ) -> DbtManifestAssetSelection:
        return DbtManifestAssetSelection.build(
            manifest=self.dbt_project.manifest_path,
            dagster_dbt_translator=self.translator,
            select=select,
            exclude=exclude,
        )

    def write_state_to_path(self, state_path: Path) -> None:
        self._project_manager.prepare(state_path)

    def build_defs_from_state(
        self, context: dg.ComponentLoadContext, state_path: Path | None
    ) -> dg.Definitions:
        project = self._project_manager.get_project(state_path)

        res_ctx = context.resolution_context

        # External mesh packages: auto-exclude their models from the materializable graph
        # by appending `package:X` to the user's own `exclude` selection. The user's
        # explicit `exclude` is preserved; we just add ours on top with a space separator.
        effective_exclude = self.exclude or ""
        if self.external_packages:
            package_exclusions = " ".join(f"package:{pkg}" for pkg in self.external_packages)
            effective_exclude = (
                f"{effective_exclude} {package_exclusions}".strip()
                if effective_exclude
                else package_exclusions
            )

        asset_specs, check_specs = build_dbt_specs(
            translator=validate_translator(self.translator),
            manifest=validate_manifest(project.manifest_path),
            select=self.select,
            exclude=effective_exclude,
            selector=self.selector,
            project=project,
            io_manager_key=None,
        )
        # State-aware tagging: when state_manifest_path is set, tag each model spec
        # with dbt/state=modified|unchanged|new based on checksum comparison against
        # a prod manifest. Users then select changed models via `tag:dbt/state=modified`.
        if self.state_manifest_path:
            asset_specs = apply_dbt_state_tags(
                asset_specs=asset_specs,
                current_manifest=validate_manifest(project.manifest_path),
                state_manifest_path=Path(self.state_manifest_path),
            )
        op_spec = self._get_op_spec(project)

        @dg.multi_asset(
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
        def _fn(context: dg.AssetExecutionContext):
            with _set_resolution_context(res_ctx):
                yield from self.execute(context=context, dbt=DbtCliResource(project))

        # dbt sources are emitted as bare AssetSpecs so that Definitions treats them as
        # external observable assets (no op, no io_manager). When another integration
        # declares the same AssetKey (Fivetran, Sling, a manual observable_source_asset),
        # Dagster merges the two — dbt contributes freshness policy, table schema, kinds.
        validated_manifest = validate_manifest(project.manifest_path)
        validated_translator = validate_translator(self.translator)
        source_specs = (
            build_dbt_source_asset_specs(
                manifest=validated_manifest,
                dagster_dbt_translator=validated_translator,
                project=project,
            )
            if self.translator.settings.enable_source_assets
            else []
        )
        # dbt exposures (dashboards, notebooks, ML models, applications, analyses) are
        # emitted as observable external AssetSpecs with deps on the referenced upstream
        # models, giving users a downstream relationship in the graph.
        exposure_specs = (
            build_dbt_exposure_asset_specs(
                manifest=validated_manifest,
                dagster_dbt_translator=validated_translator,
                project=project,
            )
            if self.translator.settings.enable_exposure_assets
            else []
        )
        # dbt semantic_models and metrics — observable external specs so users can trace
        # semantic layer lineage back to the underlying models in the graph.
        semantic_layer_specs = (
            build_dbt_semantic_layer_asset_specs(
                manifest=validated_manifest,
                dagster_dbt_translator=validated_translator,
                project=project,
            )
            if self.translator.settings.enable_semantic_layer_assets
            else []
        )
        # dbt mesh: emit stub AssetSpecs for models in imported packages. Downstream
        # models in this project still point at those keys, so lineage stays intact and
        # the upstream Dagster code location's real declarations win precedence.
        external_package_specs = build_dbt_external_package_asset_specs(
            manifest=validated_manifest,
            external_packages=self.external_packages,
            dagster_dbt_translator=validated_translator,
            project=project,
        )

        return dg.Definitions(
            assets=[
                _fn,
                *source_specs,
                *exposure_specs,
                *semantic_layer_specs,
                *external_package_specs,
            ]
        )

    def get_cli_args(self, context: dg.AssetExecutionContext) -> list[str]:
        args = resolve_cli_args(self.cli_args, context)
        if self.defer_config is not None:
            args.extend(self.defer_config.to_cli_args())
        return args

    def _get_dbt_event_iterator(
        self, context: dg.AssetExecutionContext, dbt: DbtCliResource
    ) -> DbtEventIterator[DbtDagsterEventType]:
        iterator = dbt.cli(self.get_cli_args(context), context=context).stream()
        if "column_metadata" in self.include_metadata:
            iterator = iterator.fetch_column_metadata()
        if "row_count" in self.include_metadata:
            iterator = iterator.fetch_row_counts()
        if "insights" in self.include_metadata:
            iterator = iterator.with_insights()
        return iterator

    @public
    def execute(self, context: dg.AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
        """Executes the dbt command for the selected assets.

        This method can be overridden in a subclass to customize the execution behavior,
        such as adding custom logging, modifying CLI arguments, or handling events differently.

        Args:
            context: The asset execution context provided by Dagster
            dbt: The DbtCliResource used to execute dbt commands

        Yields:
            Events from the dbt CLI execution (e.g., AssetMaterialization, AssetObservation)

        Example:
            Override this method to add custom logging before and after execution:

            .. code-block:: python

                from dagster_dbt import DbtProjectComponent
                import dagster as dg

                class CustomDbtProjectComponent(DbtProjectComponent):
                    def execute(self, context, dbt):
                        context.log.info("Starting custom dbt execution")
                        yield from super().execute(context, dbt)
                        context.log.info("Completed custom dbt execution")
        """
        yield from self._get_dbt_event_iterator(context, dbt)

    @cached_property
    def _validated_manifest(self):
        return validate_manifest(self.dbt_project.manifest_path)

    @cached_property
    def _validated_translator(self):
        return validate_translator(self.translator)

    @cached_method
    def asset_key_for_model(self, model_name: str) -> dg.AssetKey:
        dagster_dbt_translator = self._validated_translator
        manifest = self._validated_manifest

        matching_model_ids = [
            unique_id
            for unique_id, value in manifest["nodes"].items()
            if value["name"] == model_name and value["resource_type"] in ASSET_RESOURCE_TYPES
        ]

        if len(matching_model_ids) == 0:
            raise KeyError(f"Could not find a dbt model, seed, or snapshot with name: {model_name}")

        return dagster_dbt_translator.get_asset_spec(
            manifest,
            next(iter(matching_model_ids)),
            self.dbt_project,
        ).key


class DbtProjectComponentTranslator(
    create_component_translator_cls(DbtProjectComponent, DagsterDbtTranslator),  # ty: ignore[unsupported-base]
    ComponentTranslator[DbtProjectComponent],
):
    def __init__(
        self,
        component: DbtProjectComponent,
        settings: DagsterDbtComponentTranslatorSettings | None,
    ):
        self._component = component
        super().__init__(settings)

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: DbtProject | None
    ) -> dg.AssetSpec:
        base_spec = super().get_asset_spec(manifest, unique_id, project)
        if self.component.translation is None:
            spec = base_spec
        else:
            dbt_props = get_node(manifest, unique_id)
            spec = self.component.translation(base_spec, dbt_props)
        return spec.merge_attributes(metadata={DAGSTER_DBT_TRANSLATOR_METADATA_KEY: self})


def get_projects_from_dbt_component(components: Path) -> list[DbtProject]:
    project_components = ComponentTree.for_project(components).get_all_components(
        of_type=DbtProjectComponent
    )

    return [component.dbt_project for component in project_components]
