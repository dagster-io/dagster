from dagster._core.definitions.asset_check_spec import AssetCheckSpec as AssetCheckSpec
from dagster._core.definitions.asset_key import AssetKey
from dagster.components import Resolvable
from dagster.components.resolved.core_models import ResolvedAssetCheckSpec
from dagster_shared.record import record


@record
class ContainsAssetChecks(Resolvable):
    checks: list[ResolvedAssetCheckSpec]


def test_parse_asset_checks() -> None:
    contains_asset_checks = ContainsAssetChecks.resolve_from_dict(
        {
            "checks": [
                {
                    "name": "my_check",
                    "asset": "my_asset",
                }
            ]
        }
    )

    assert len(contains_asset_checks.checks) == 1

    check_spec = contains_asset_checks.checks[0]

    assert check_spec.name == "my_check"
    assert check_spec.asset_key == AssetKey("my_asset")
