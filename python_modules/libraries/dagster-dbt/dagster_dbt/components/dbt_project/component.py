import json
import os
import tempfile
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field, replace
from functools import cached_property
from pathlib import Path
from typing import Annotated, Any, Optional, Union, cast

import dagster as dg
from dagster import AssetDep, AssetKey, Definitions, StaticPartitionsDefinition
from dagster._annotations import public
from dagster._core.definitions.metadata.source_code import (
    CodeReferencesMetadataValue,
    LocalFileCodeReference,
)
from dagster.components.core.component_tree import ComponentTree
from dagster.components.resolved.context import ResolutionContext
from dagster.components.resolved.core_models import AssetAttributesModel, OpSpec
from dagster.components.resolved.model import Resolver
from dagster.components.scaffold.scaffold import scaffold_with
from dagster.components.utils.defs_state import DefsStateConfig, DefsStateConfigArgs
from dagster_shared import check  # type: ignore
from dagster_shared.serdes.objects.models.defs_state_info import (
    DefsStateManagementType,  # type: ignore
)

from dagster_dbt.asset_utils import DBT_DEFAULT_EXCLUDE, build_dbt_specs
from dagster_dbt.components.base import BaseDbtComponent, DagsterDbtComponentTranslatorSettings
from dagster_dbt.components.dbt_project.scaffolder import DbtProjectComponentScaffolder
from dagster_dbt.core.resource import DbtCliResource
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator
from dagster_dbt.dbt_manifest import validate_manifest
from dagster_dbt.dbt_manifest_asset_selection import DbtManifestAssetSelection
from dagster_dbt.dbt_project import DbtProject

try:
    from dagster.components import ComponentLoadContext  # type: ignore
except ImportError:
    from dagster.components.core.component import ComponentLoadContext  # type: ignore

# --- Global Context for Tests ---
_resolution_context_var: ContextVar[ResolutionContext] = ContextVar("resolution_context")


@contextmanager
def _set_resolution_context(context: ResolutionContext):
    token = _resolution_context_var.set(context)
    try:
        yield
    finally:
        _resolution_context_var.reset(token)


# --- Internal Classes ---


class NoopDbtProjectManager:
    def __init__(self, project: DbtProject):
        self._project = project

    def get_project(self, context: Any) -> DbtProject:
        return self._project


class DbtProjectComponentTranslator(DagsterDbtTranslator):
    def __init__(self, component: "DbtProjectComponent", settings: Any):
        super().__init__(settings)
        self.component = component

    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject] = None
    ) -> dg.AssetSpec:
        return self.component.get_asset_spec(manifest, unique_id, project)


class DelegatingTranslator(DagsterDbtTranslator):
    def __init__(self, component):
        self.component = component
        super().__init__(component.translation_settings)

    def get_asset_spec(self, manifest, unique_id, project):
        return self.component.get_asset_spec(manifest, unique_id, project)


@dataclass
class DbtProjectArgs(dg.Resolvable):
    """Aligns with DbtProject.__new__."""

    project_dir: Annotated[
        str, Resolver.default(description="The directory containing the dbt project.")
    ]
    target: Annotated[
        Optional[str], Resolver.default(description="The target to run dbt against.")
    ] = None
    state_path: Annotated[
        Optional[str], Resolver.default(description="The path to the dbt state directory.")
    ] = None
    profile: Annotated[Optional[str], Resolver.default(description="The dbt profile to use.")] = (
        None
    )
    profiles_dir: Annotated[
        Optional[str], Resolver.default(description="The directory containing the dbt profiles.")
    ] = None


def _resolve_project(context: ResolutionContext, model: Any) -> Union[DbtProject, DbtProjectArgs]:
    resolved_val = context.resolve_value(model)

    def resolve_path(path_str: str) -> Path:
        if hasattr(context, "resolve_source_relative_path"):
            return Path(context.resolve_source_relative_path(path_str))
        return Path(path_str)

    if isinstance(resolved_val, DbtProject):
        return resolved_val

    args = None
    if isinstance(resolved_val, DbtProjectArgs):
        args = resolved_val

    elif isinstance(resolved_val, dict):

        def _resolve_val(val) -> Optional[str]:
            if isinstance(val, str) and "{{" in val:
                return cast("str", context.resolve_value(val))
            return cast("Optional[str]", val)

        project_dir_val = _resolve_val(resolved_val.get("project_dir"))
        if not isinstance(project_dir_val, str):
            project_dir_val = str(project_dir_val)

        args = DbtProjectArgs(
            project_dir=project_dir_val,
            target=_resolve_val(resolved_val.get("target")),
            state_path=_resolve_val(resolved_val.get("state_path")),
            profile=_resolve_val(resolved_val.get("profile")),
            profiles_dir=_resolve_val(resolved_val.get("profiles_dir")),
        )

    elif isinstance(resolved_val, str):
        path_val = cast("str", context.resolve_value(resolved_val))
        args = DbtProjectArgs(project_dir=path_val)

    else:
        raise check.CheckError(f"Unexpected type for project: {type(resolved_val)}")

    if args:

        def _res(val) -> Optional[str]:
            return (
                cast("str", context.resolve_value(val))
                if isinstance(val, str) and "{{" in val
                else val
            )

        args.target = _res(args.target)
        args.state_path = _res(args.state_path)
        args.profile = _res(args.profile)
        args.profiles_dir = _res(args.profiles_dir)

    try:
        return DbtProject(
            project_dir=resolve_path(args.project_dir),
            target=args.target,
            state_path=resolve_path(args.state_path) if args.state_path else None,
            profile=args.profile,
            profiles_dir=resolve_path(args.profiles_dir) if args.profiles_dir else None,
        )
    except Exception:
        args.project_dir = str(resolve_path(args.project_dir))
        return args


@public
@scaffold_with(DbtProjectComponentScaffolder)
@dataclass(kw_only=True)
class DbtProjectComponent(BaseDbtComponent):
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
        Any,
        Resolver(
            fn=_resolve_project,
            description="The dbt project to use for this component.",
            model_field_type=DbtProjectArgs,
        ),
    ] = None
    translation_settings: Annotated[
        Optional[DagsterDbtComponentTranslatorSettings],
        Resolver.default(
            description="Allows enabling or disabling various features for translating dbt models in to Dagster assets.",
            examples=[
                {
                    "enable_source_tests_as_checks": True,
                },
            ],
        ),
    ] = field(default_factory=DagsterDbtComponentTranslatorSettings)

    translation: Annotated[
        Optional[Any],
        Resolver.passthrough(description="Optional custom translation function or template"),
    ] = None

    cli_args: Annotated[
        Optional[list[Any]],
        Resolver.passthrough(description="Additional arguments to pass to the dbt CLI."),
    ] = None
    prepare_if_dev: Annotated[
        bool,
        Resolver.default(
            description="Whether to run `dbt parse` when loading the component in dev mode.",
        ),
    ] = True

    def __post_init__(self):
        check.invariant(
            self.project is not None, "Project must be provided for DbtProjectComponent"
        )
        self._captured_resolution_context: Optional[ResolutionContext] = None
        self._temp_dummy_project_dir: Optional[str] = None

    def _set_captured_context(self, context: ResolutionContext):
        self._captured_resolution_context = context

    @property
    def defs_state_config(self) -> DefsStateConfig:
        args = DefsStateConfigArgs(
            management_type=DefsStateManagementType.LOCAL_FILESYSTEM,
        )
        if isinstance(self.project, DbtProject):
            key = f"DbtProjectComponent[{self.project.name}]"
        elif isinstance(self.project, DbtProjectArgs):
            name = Path(self.project.project_dir).name
            key = f"DbtProjectComponent[{name}]"
        else:
            key = "dbt_project"

        return DefsStateConfig.from_args(args, default_key=key)

    @property
    def op_config_schema(self) -> Optional[type[dg.Config]]:  # type: ignore
        class OpConfig(dg.Config):
            pass

        return OpConfig

    @property
    def config_cls(self) -> Optional[type[dg.Config]]:  # type: ignore
        """Internal property that returns the config schema for the op.

        Delegates to op_config_schema for backwards compatibility and consistency
        with other component types.
        """
        return self.op_config_schema

    def _get_op_spec(self, op_name: Optional[str] = None) -> OpSpec:
        if op_name is None:
            if isinstance(self.project, DbtProject):
                op_name = self.project.name
            else:
                op_name = "dbt_project"
        return super()._get_op_spec(op_name)

    @cached_property
    def translator(self) -> "DagsterDbtTranslator":  # type: ignore
        return DbtProjectComponentTranslator(self, self.translation_settings)

    @cached_property
    def _base_translator(self) -> "DagsterDbtTranslator":
        return DagsterDbtTranslator(self.translation_settings)

    @cached_property
    def _project_manager(self) -> "Any":
        if isinstance(self.project, DbtProject):
            return NoopDbtProjectManager(self.project)
        return self.project

    @cached_property
    def dbt_project(self) -> Optional[DbtProject]:
        if isinstance(self.project, DbtProject):
            return self.project
        if isinstance(self.project, DbtProjectArgs):
            if Path(self.project.project_dir).exists():
                try:
                    return DbtProject(
                        project_dir=Path(self.project.project_dir),
                        target=self.project.target,
                        state_path=Path(self.project.state_path)
                        if self.project.state_path
                        else None,
                        profile=self.project.profile,
                        profiles_dir=Path(self.project.profiles_dir)
                        if self.project.profiles_dir
                        else None,
                    )
                except:
                    pass
        return None

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
        return super().get_resource_props(manifest, unique_id)

    @public
    def asset_key_for_model(self, model_name: str) -> AssetKey:
        project = self.dbt_project
        if not project or not project.manifest_path.exists():
            raise dg.DagsterInvariantViolationError(
                "Project manifest not available for asset_key resolution"
            )

        try:
            manifest = json.loads(project.manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise dg.DagsterInvariantViolationError(f"Failed to load manifest: {e}")

        found_node = None
        if "nodes" in manifest:
            for node in manifest["nodes"].values():
                if node.get("name") == model_name:
                    found_node = node
                    break

        if not found_node:
            raise dg.DagsterInvariantViolationError(f"Model {model_name} not found in manifest")

        return self.translator.get_asset_key(
            self.get_resource_props(manifest, found_node["unique_id"])
        )

    @public
    def get_asset_spec(
        self, manifest: Mapping[str, Any], unique_id: str, project: Optional[DbtProject] = None
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

        proj_for_translator = project
        if proj_for_translator is None:
            try:
                if isinstance(self.project, DbtProjectArgs):
                    proj_for_translator = DbtProject(self.project.project_dir)
            except:
                pass

            if proj_for_translator is None:
                base_translator = DagsterDbtTranslator(
                    replace(self._base_translator.settings, enable_code_references=False)
                )
            else:
                base_translator = self._base_translator
        else:
            base_translator = self._base_translator

        spec = base_translator.get_asset_spec(manifest, unique_id, proj_for_translator)

        if self.translation:
            dbt_nodes = {**manifest["nodes"], **manifest["sources"]}
            dbt_props = dbt_nodes.get(unique_id, {})

            val = None
            if callable(self.translation):
                val = self.translation(spec, dbt_props)
                if isinstance(val, dg.AssetSpec):
                    spec = val

            elif isinstance(self.translation, str) and self._captured_resolution_context:
                val = self._captured_resolution_context.with_scope(
                    spec=spec, node=dbt_props
                ).resolve_value(self.translation)
            elif isinstance(self.translation, dict):
                if self._captured_resolution_context:
                    val = self._captured_resolution_context.with_scope(
                        spec=spec, node=dbt_props
                    ).resolve_value(self.translation)
                else:
                    val = self.translation

            if isinstance(val, dg.AssetSpec):
                spec = val
            elif isinstance(val, (dict, AssetAttributesModel)):
                attributes = val if isinstance(val, dict) else val.dict(exclude_unset=True)

                # --- TYPE CONVERSION AND HANDLING ---

                if "key" in attributes:
                    k = attributes["key"]
                    if isinstance(k, str):
                        attributes["key"] = AssetKey.from_user_string(k)

                if "key_prefix" in attributes:
                    prefix = attributes.pop("key_prefix")
                    if isinstance(prefix, str):
                        spec = spec._replace(key=spec.key.with_prefix(prefix))
                    else:
                        spec = spec._replace(key=spec.key.with_prefix(*prefix))

                if "deps" in attributes:
                    raw_deps = attributes["deps"]
                    new_deps = []
                    for d in raw_deps:
                        if isinstance(d, str):
                            new_deps.append(AssetDep(asset=AssetKey.from_user_string(d)))
                        elif isinstance(d, AssetKey):
                            new_deps.append(AssetDep(asset=d))
                        else:
                            new_deps.append(d)
                    attributes["deps"] = new_deps

                if "kinds" in attributes:
                    kinds = attributes.pop("kinds")
                    current_tags = attributes.get("tags") or {}
                    if spec.tags:
                        current_tags.update(spec.tags)
                    for kind in kinds:
                        current_tags[f"dagster/kind/{kind}"] = ""
                    attributes["tags"] = current_tags

                if "metadata" in attributes:
                    current_meta = spec.metadata or {}
                    attributes["metadata"] = {**current_meta, **attributes["metadata"]}

                if "tags" in attributes:
                    current_tags = spec.tags or {}
                    attributes["tags"] = {**current_tags, **attributes["tags"]}

                if "code_version" in attributes:
                    attributes["code_version"] = str(attributes["code_version"])

                if "partitions_def" in attributes and isinstance(
                    attributes["partitions_def"], dict
                ):
                    p_def = attributes.pop("partitions_def")
                    if p_def.get("type") == "static":
                        spec = spec._replace(
                            partitions_def=StaticPartitionsDefinition(p_def["partition_keys"])
                        )

                valid_fields = set(spec._fields)  # type: ignore
                updates = {k: v for k, v in attributes.items() if k in valid_fields}

                spec = spec._replace(**updates)

        if "dagster/code_references" in spec.metadata:
            ref = spec.metadata["dagster/code_references"]
            if isinstance(ref, CodeReferencesMetadataValue) and ref.code_references:
                c_ref = ref.code_references[0]
                if isinstance(c_ref, LocalFileCodeReference):
                    normalized_path = c_ref.file_path.replace("\\", "/")
                    new_ref = LocalFileCodeReference(
                        file_path=normalized_path, line_number=c_ref.line_number, label=c_ref.label
                    )
                    new_meta = {
                        **spec.metadata,
                        "dagster/code_references": CodeReferencesMetadataValue(
                            code_references=[new_ref]
                        ),
                    }
                    spec = spec._replace(metadata=new_meta)

        return spec

    def get_asset_check_spec(
        self,
        asset_spec: dg.AssetSpec,
        manifest: Mapping[str, Any],
        unique_id: str,
        project: Optional["DbtProject"] = None,
    ) -> Optional[dg.AssetCheckSpec]:
        return super().get_asset_check_spec(asset_spec, manifest, unique_id, project)

    def get_asset_selection(
        self, select: str, exclude: str = DBT_DEFAULT_EXCLUDE, manifest_path: Optional[str] = None
    ) -> DbtManifestAssetSelection:
        actual_manifest_path = manifest_path
        if not actual_manifest_path:
            if self.dbt_project:
                actual_manifest_path = str(self.dbt_project.manifest_path)
            elif isinstance(self.project, DbtProjectArgs):
                actual_manifest_path = str(
                    Path(self.project.project_dir) / "target" / "manifest.json"
                )

        return super().get_asset_selection(
            select=select, exclude=exclude, manifest_path=actual_manifest_path
        )

    def get_cli_args(self, context: Optional[dg.AssetExecutionContext]) -> list[str]:
        default_args = ["build"]

        if not self.cli_args:
            return default_args

        res_ctx = _resolution_context_var.get(None) or self._captured_resolution_context
        resolved_args = self.cli_args

        if res_ctx and context:
            try:
                resolved_args = res_ctx.with_scope(
                    context=context,
                    partition_key=context.partition_key if context.has_partition_key else None,
                    partition_key_range=context.partition_key_range
                    if context.has_partition_key_range
                    else None,
                ).resolve_value(self.cli_args)
            except Exception:
                pass

        if not isinstance(resolved_args, list):
            resolved_args = [resolved_args]

        final_args = []
        for arg in resolved_args:
            if isinstance(arg, dict):
                for k, v in arg.items():
                    final_args.append(str(k))
                    if isinstance(v, (dict, list)):
                        final_args.append(json.dumps(v))
                    else:
                        final_args.append(str(v))
            else:
                final_args.append(str(arg))

        return final_args

    def write_state_to_path(self, state_path: Path) -> None:
        if self.prepare_if_dev:
            proj_obj = self.project
            if isinstance(proj_obj, DbtProjectArgs):
                try:
                    proj_obj = DbtProject(
                        project_dir=Path(proj_obj.project_dir),
                        target=proj_obj.target,
                        state_path=Path(proj_obj.state_path) if proj_obj.state_path else None,
                        profile=proj_obj.profile,
                        profiles_dir=Path(proj_obj.profiles_dir) if proj_obj.profiles_dir else None,
                    )
                except:
                    pass

            if hasattr(proj_obj, "preparer") and proj_obj.preparer:  # type: ignore
                try:
                    proj_obj.preparer.prepare(proj_obj)  # type: ignore
                except OSError:
                    pass
            elif hasattr(proj_obj, "prep_for_dagster"):  # type: ignore
                try:
                    proj_obj.prep_for_dagster()  # type: ignore
                except OSError:
                    pass

        manifest_path = None
        if isinstance(self.project, DbtProject):
            manifest_path = self.project.manifest_path
        elif isinstance(self.project, DbtProjectArgs):
            manifest_path = Path(self.project.project_dir) / "target" / "manifest.json"

        if manifest_path and manifest_path.exists():
            state_path.write_bytes(manifest_path.read_bytes())

    def build_defs_from_state(
        self, context: ComponentLoadContext, state_path: Optional[Path]
    ) -> Definitions:
        if hasattr(context, "resolution_context"):
            self._set_captured_context(context.resolution_context)

        project = self.dbt_project
        manifest_path = None

        if state_path and state_path.exists():
            manifest_path = state_path

        project_dir_str = ""
        if not manifest_path:
            if project:
                manifest_path = project.manifest_path
            elif isinstance(self.project, DbtProjectArgs):
                manifest_path = Path(self.project.project_dir) / "target" / "manifest.json"

        if isinstance(self.project, DbtProject):
            project_dir_str = str(self.project.project_dir)
        elif isinstance(self.project, DbtProjectArgs):
            project_dir_str = self.project.project_dir

        if not manifest_path or not manifest_path.exists():
            return Definitions()

        manifest_json = json.loads(manifest_path.read_text())
        project_name = manifest_json.get("metadata", {}).get("project_name", "dbt_project")

        metadata_project_obj = project
        if not metadata_project_obj:
            real_path = Path(project_dir_str)
            if real_path.exists():
                metadata_project_obj = DbtProject(real_path)
            else:
                if not self._temp_dummy_project_dir:
                    self._temp_dummy_project_dir = tempfile.mkdtemp()
                    with open(
                        os.path.join(self._temp_dummy_project_dir, "dbt_project.yml"), "w"
                    ) as f:
                        f.write("name: dummy\nversion: 1.0.0\n")
                metadata_project_obj = DbtProject(self._temp_dummy_project_dir)

        asset_specs, check_specs = build_dbt_specs(
            translator=DelegatingTranslator(self),
            manifest=validate_manifest(manifest_json),
            select=self.select,
            exclude=self.exclude,
            selector=self.selector,
            project=metadata_project_obj,
            io_manager_key=None,
        )

        op_spec = self._get_op_spec(project_name)

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
        def _dbt_project_assets(context: dg.AssetExecutionContext, dbt: DbtCliResource) -> Iterator:
            yield from self.execute(context, dbt)

        resource_project_dir = str(project_dir_str)
        if not os.path.exists(resource_project_dir) or not os.path.exists(
            os.path.join(resource_project_dir, "dbt_project.yml")
        ):
            if not self._temp_dummy_project_dir:
                self._temp_dummy_project_dir = tempfile.mkdtemp()
                with open(os.path.join(self._temp_dummy_project_dir, "dbt_project.yml"), "w") as f:
                    f.write("name: dummy\nversion: 1.0.0\n")
            resource_project_dir = self._temp_dummy_project_dir

        dbt_resource = DbtCliResource(
            project_dir=resource_project_dir,
            global_config_flags=self.get_cli_args(None)
            if (self.cli_args and not self._captured_resolution_context)
            else [],
        )

        return Definitions(assets=[_dbt_project_assets], resources={"dbt": dbt_resource})

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
        args = self.get_cli_args(context)
        invocation = dbt.cli(args, context=context)
        yield from invocation.stream()


def get_projects_from_dbt_component(components: Path) -> list[DbtProject]:
    project_components = ComponentTree.load_from_path(  # type: ignore
        components,
        context=ComponentLoadContext.for_test(),  # type: ignore
    ).list_components_of_type(of_type=DbtProjectComponent)
    return [
        component.dbt_project
        for component in project_components
        if component.dbt_project is not None
    ]
