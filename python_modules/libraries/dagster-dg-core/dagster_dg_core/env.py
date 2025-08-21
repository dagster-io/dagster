from collections import defaultdict
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, Optional

from dagster_shared import check
from typing_extensions import Self

from dagster_dg_core.context import DgContext


def get_specified_env_var_deps(component_data: Mapping[str, Any]) -> set[str]:
    if "requirements" not in component_data or "env" not in component_data["requirements"]:
        return set()
    return set(component_data["requirements"]["env"])


def get_project_specified_env_vars(dg_context: DgContext) -> Mapping[str, Sequence[Path]]:
    """Returns a mapping of environment variables to the components that specify
    requiring them.
    """
    if not dg_context.has_defs_path:
        return {}

    from dagster_shared.yaml_utils import parse_yamls_with_source_position
    from yaml.scanner import ScannerError

    env_vars = defaultdict(list)

    for component_dir in dg_context.defs_path.rglob("*"):
        defs_path = component_dir / "defs.yaml"

        if defs_path.exists():
            text = defs_path.read_text()
            try:
                component_doc_trees = parse_yamls_with_source_position(
                    text, filename=str(defs_path)
                )
            except ScannerError:
                continue

            for component_doc_tree in component_doc_trees:
                specified_env_var_deps = get_specified_env_var_deps(component_doc_tree.value)
                for key in specified_env_var_deps:
                    env_vars[key].append(defs_path.relative_to(dg_context.defs_path).parent)
    return env_vars


class ProjectEnvVars:
    """Represents the environment for a project, stored in the .env file of a
    project root.
    """

    def __init__(self, ctx: DgContext, values: Mapping[str, Optional[str]]):
        self.ctx = ctx
        self._values = values

    @classmethod
    def empty(cls, ctx: DgContext) -> "Self":
        return cls(ctx, values={})

    @classmethod
    def from_ctx(cls, ctx: DgContext) -> "Self":
        check.invariant(ctx.is_project, "ProjectEnvVars can only be created from a project context")
        from dotenv import dotenv_values

        env_path = ctx.root_path / ".env"
        if not env_path.exists():
            return cls(ctx, values={})
        env = dotenv_values(env_path)
        return cls(ctx, values=env)

    @property
    def values(self) -> Mapping[str, Optional[str]]:
        return self._values

    def get(self, key: str) -> Optional[str]:
        return self.values.get(key)

    def with_values(self, values: Mapping[str, Optional[str]]) -> "ProjectEnvVars":
        return ProjectEnvVars(self.ctx, {**self.values, **values})

    def without_values(self, keys: set[str]) -> "ProjectEnvVars":
        return ProjectEnvVars(self.ctx, {k: v for k, v in self.values.items() if k not in keys})

    def write(self) -> None:
        env_path = self.ctx.root_path / ".env"
        env_path.write_text(
            "\n".join([f"{key}={value}" for key, value in self.values.items() if value is not None])
        )
