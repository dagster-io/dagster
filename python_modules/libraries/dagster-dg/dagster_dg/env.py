from typing import Optional

from dagster_shared import check
from dotenv import dotenv_values
from typing_extensions import Self

from dagster_dg.context import DgContext


class Env:
    def __init__(self, ctx: DgContext, values: dict[str, Optional[str]]):
        self.ctx = ctx
        self.values = values

    @classmethod
    def from_ctx(cls, ctx: DgContext) -> "Self":
        check.invariant(ctx.is_project, "Env can only be created from a project context")
        env_path = ctx.root_path / ".env"
        if not env_path.exists():
            return cls(ctx, values={})
        env = dotenv_values(env_path)
        return cls(ctx, values=env)

    def get(self, key: str) -> Optional[str]:
        return self.values.get(key)

    def with_values(self, values: dict[str, Optional[str]]) -> "Env":
        return Env(self.ctx, {**self.values, **values})

    def without_values(self, keys: set[str]) -> "Env":
        return Env(self.ctx, {k: v for k, v in self.values.items() if k not in keys})

    def write(self) -> None:
        env_path = self.ctx.root_path / ".env"
        env_path.write_text(
            "\n".join([f"{key}={value}" for key, value in self.values.items() if value is not None])
        )
