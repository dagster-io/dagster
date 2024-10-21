import pytest
from dagster._core.definitions.asset_key import AssetCheckKey, AssetKey, entity_key_from_db_string


@pytest.mark.parametrize(
    "check_key,expected",
    [
        (AssetKey("a"), '["a"]'),
        (AssetKey(['a/b/c"d', 'e":-.f']), '["a/b/c\\"d", "e\\":-.f"]'),
        (AssetCheckKey(AssetKey("a"), "b"), '{"asset_key": "[\\"a\\"]", "check_name": "b"}'),
        (
            AssetCheckKey(AssetKey(['a/b/c"d', 'e":-.f']), "b9!*:z7)'&xz\"./x/y"),
            '{"asset_key": "[\\"a/b/c\\\\\\"d\\", \\"e\\\\\\":-.f\\"]", "check_name": "b9!*:z7)\'&xz\\"./x/y"}',
        ),
    ],
)
def test_valid_db_strings(check_key: AssetCheckKey, expected: str) -> None:
    """Note: the expected string values should never be updated, as they are
    stored in the database forever.
    """
    assert check_key.to_db_string() == expected
    assert entity_key_from_db_string(check_key.to_db_string()) == check_key


def test_invalid_db_strings() -> None:
    # note: AssetKey has a catch-all method for converting any string to an asset key,
    # so we're just making sure that that holds up and doesn't produce weird AssetCheckKeys
    assert entity_key_from_db_string("random_stuff") == AssetKey("random_stuff")
    assert entity_key_from_db_string('{"asset_key": "[\\"a\\"]"}') == AssetKey(["asset_key", "a"])
    assert entity_key_from_db_string(
        '{"asset_key": "[\\"a\\"]", "check_name": "b", "other": 1}'
    ) == AssetKey(["asset_key", "a", "check_name", "b", "other", "1"])
