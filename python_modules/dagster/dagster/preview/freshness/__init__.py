from dagster._core.definitions.assets.definition.asset_spec import (
    apply_freshness_policy as apply_freshness_policy,
)
from dagster._core.definitions.freshness import InternalFreshnessPolicy as FreshnessPolicy

__all__ = [
    "FreshnessPolicy",
    "apply_freshness_policy",
]
