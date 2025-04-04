from dagster._core.definitions.asset_check_spec import AssetCheckSpec
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey
from dagster._core.definitions.definitions_class import Definitions

from components_yaml_checks_dsl.definitions import defs


def checks_specs_by_key(defs: Definitions) -> dict[str, AssetCheckSpec]:
    """Return a dictionary of check specs by key."""
    check_specs = {}
    asset_graph = defs.get_asset_graph()

    for check_key in asset_graph.asset_check_keys:
        check_spec = asset_graph.get_check_spec(check_key)
        check_specs[check_key] = check_spec
    return check_specs


def raw_user_ck(table: str, check_name: str) -> AssetCheckKey:
    """Return an AssetCheckKey for the given table and check name."""
    return AssetCheckKey(
        asset_key=AssetKey(["RAW_DATA", table]),
        name=check_name,
    )


def test_load_defs() -> None:
    defs_obj = defs()
    assert isinstance(defs_obj, Definitions)

    check_specs = checks_specs_by_key(defs_obj)
    assert raw_user_ck("users", "user_count_static_threshold") in check_specs
