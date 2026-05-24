import itertools
import tokenize
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

from pydantic import Field

from dagster import AssetExecutionContext, AssetKey, PipesExecutionResult, multi_asset
from dagster._core.definitions.assets.definition.asset_spec import AssetSpec
from dagster._core.definitions.assets.definition.assets_definition import AssetsDefinition
from dagster._core.definitions.definitions_class import Definitions
from dagster._utils.names import clean_name
from dagster.components.component.component import Component
from dagster.components.core.context import ComponentLoadContext
from dagster.components.resolved.base import Model, Resolvable
from dagster.components.resolved.core_models import OpSpec, ResolvedAssetSpec


class ScriptConfig(Resolvable, Model):
    op: Optional[OpSpec] = Field(default=None, description="The op spec for the script.")
    specs: Optional[Sequence[ResolvedAssetSpec]] = Field(
        default=None, description="The asset specs for the script."
    )


class ScriptCollectionComponent(Component, Resolvable, Model):
    include: list[str] = Field(
        default=["**/*"],
        description="The glob patterns to include in the collection.",
        examples=[["*.py"], ["subdir/**", "include.py"]],
    )
    exclude: list[str] = Field(
        default_factory=list,
        description="The glob patterns to exclude from the collection.",
        examples=[["*.txt"], ["utils/**", "dont_include.py"]],
    )

    def _get_script_paths(self, context: ComponentLoadContext) -> list[Path]:
        base_path = Path(context.path)
        include_paths = set(itertools.chain(*[base_path.glob(pattern) for pattern in self.include]))
        exclude_paths = set(itertools.chain(*[base_path.glob(pattern) for pattern in self.exclude]))
        return [
            path
            for path in (include_paths - exclude_paths - {context.path / "defs.yaml"})
            if path.is_file()
        ]

    def _parse_script_config(self, script_path: Path) -> str:
        """Parses the PEP-731 `# /// dagster` block at the top of a script file."""
        lines = []
        in_block = False
        with script_path.open() as f:
            for tok in tokenize.generate_tokens(f.readline):
                if tok.type == tokenize.COMMENT:
                    content = tok.string.lstrip("#")
                    # found start of block
                    if content.strip() == "/// dagster":
                        in_block = True
                    elif in_block:
                        # found end of block
                        if content.strip().startswith("///"):
                            break
                        lines.append(content)
                elif tok.type not in (tokenize.NEWLINE, tokenize.NL):
                    break

        return "\n".join(lines)

    def _get_op_and_specs(
        self, context: ComponentLoadContext, script_path: Path
    ) -> tuple[OpSpec, Sequence[AssetSpec]]:
        script_config = self._parse_script_config(script_path)

        def _script_key(path: str) -> AssetKey:
            # resolve the path relative to context.path
            _, specs = self._get_op_and_specs(context, context.path / path)
            if len(specs) != 1:
                raise ValueError(
                    f"Expected exactly 1 asset spec from script {path}, got {len(specs)}"
                )
            return specs[0].key

        model = ScriptConfig.resolve_from_yaml(
            script_config,
            scope={
                **context.resolution_context.scope,
                # Allows for {{ script("path/to/script.py") }} in the script config
                "script": _script_key,
            },
        )
        op_spec = self.get_op_spec(context, model, script_path)
        asset_specs = self.get_asset_specs(context, model, script_path)
        return op_spec, asset_specs

    def get_op_spec(
        self, context: ComponentLoadContext, script_config: ScriptConfig, script_path: Path
    ) -> OpSpec:
        if script_config.op:
            return script_config.op

        relpath = script_path.relative_to(context.path)
        default_name = clean_name("_".join(relpath.with_suffix("").parts))
        return OpSpec(name=default_name)

    def get_asset_specs(
        self, context: ComponentLoadContext, script_config: ScriptConfig, script_path: Path
    ) -> Sequence[AssetSpec]:
        if script_config.specs:
            return script_config.specs

        relpath = script_path.relative_to(context.path)
        default_key = AssetKey(relpath.with_suffix("").parts)
        return script_config.specs or [AssetSpec(key=default_key)]

    def launch_script(
        self, context: AssetExecutionContext, script_path: Path
    ) -> Sequence[PipesExecutionResult]:
        # TODO: make configurable
        from dagster._core.pipes.subprocess import PipesSubprocessClient

        return (
            PipesSubprocessClient()
            .run(command=["python", str(script_path)], context=context.op_execution_context)
            .get_results()
        )

    def _build_asset(self, context: ComponentLoadContext, script_path: Path) -> AssetsDefinition:
        op, specs = self._get_op_and_specs(context, script_path)

        @multi_asset(
            name=op.name,
            description=op.description,
            op_tags=op.tags,
            backfill_policy=op.backfill_policy,
            specs=specs,
        )
        def _asset(context: AssetExecutionContext):
            yield from self.launch_script(context, script_path)

        return _asset

    def build_defs(self, context: ComponentLoadContext) -> Definitions:
        assets = [
            self._build_asset(context, script_path)
            for script_path in self._get_script_paths(context)
        ]
        return Definitions(assets=assets)
