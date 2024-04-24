from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Generator, Optional

from dagster._core.definitions.auto_materialize_policy import AutoMaterializePolicy
from dagster._core.definitions.backfill_policy import BackfillPolicy
from dagster._model import DagsterModel


@contextmanager
def default_asset_attrs(
    group_name: Optional[str] = None,
    auto_materialize_policy: Optional[AutoMaterializePolicy] = None,
    backfill_policy: Optional[BackfillPolicy] = None,
) -> Generator[Any, None, None]:
    obj = DefaultAssetAttrs(
        group_name=group_name,
        auto_materialize_policy=auto_materialize_policy,
        backfill_policy=backfill_policy,
    )
    outer = default_asset_attrs_context.get()
    inner = outer.merge(obj)
    default_asset_attrs_context.set(inner)
    try:
        yield
    finally:
        default_asset_attrs_context.set(outer)


class DefaultAssetAttrs(DagsterModel):
    group_name: Optional[str]
    auto_materialize_policy: Optional[AutoMaterializePolicy]
    backfill_policy: Optional[BackfillPolicy]

    def merge(self, other: "DefaultAssetAttrs") -> "DefaultAssetAttrs":
        return DefaultAssetAttrs(
            group_name=other.group_name or self.group_name,
            auto_materialize_policy=other.auto_materialize_policy or self.auto_materialize_policy,
            backfill_policy=other.backfill_policy or self.backfill_policy,
        )


default_asset_attrs_context: ContextVar[DefaultAssetAttrs] = ContextVar(
    "default_asset_attrs_context",
    default=DefaultAssetAttrs(
        group_name=None,
        auto_materialize_policy=None,
        backfill_policy=None,
    ),
)
