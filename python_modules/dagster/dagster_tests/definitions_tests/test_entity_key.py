import dagster as dg
import pytest
from dagster._core.definitions.asset_key import (
    AssetCheckKey,
    AssetJobKey,
    entity_key_from_db_string,
)


@pytest.mark.parametrize(
    "check_key,expected",
    [
        (dg.AssetKey("a"), '["a"]'),
        (dg.AssetKey(['a/b/c"d', 'e":-.f']), '["a/b/c\\"d", "e\\":-.f"]'),
        (dg.AssetCheckKey(dg.AssetKey("a"), "b"), '{"asset_key": "[\\"a\\"]", "check_name": "b"}'),
        (
            dg.AssetCheckKey(dg.AssetKey(['a/b/c"d', 'e":-.f']), "b9!*:z7)'&xz\"./x/y"),
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


@pytest.mark.parametrize(
    "job_key,expected_db",
    [
        (AssetJobKey("my_job"), '{"job_name": "my_job"}'),
        (AssetJobKey("a/b"), '{"job_name": "a/b"}'),
    ],
)
def test_asset_job_key_db_strings(job_key: AssetJobKey, expected_db: str) -> None:
    assert job_key.to_db_string() == expected_db
    assert entity_key_from_db_string(job_key.to_db_string()) == job_key


def test_asset_job_key_serdes_roundtrip() -> None:
    key = AssetJobKey("my_job")
    assert dg.deserialize_value(dg.serialize_value(key), AssetJobKey) == key


def test_asset_job_key_user_string_roundtrip() -> None:
    key = AssetJobKey("my_job")
    assert key.to_user_string() == "my_job"
    assert AssetJobKey.from_user_string("my_job") == key


@pytest.mark.parametrize(
    "check_key",
    [
        dg.AssetCheckKey(dg.AssetKey("a"), "b"),
        dg.AssetCheckKey(dg.AssetKey(["prefix", "asset1"]), "freshness_check"),
        # Asset keys can contain colons. For example the dagster-looker integration emits
        # keys such as AssetKey(["my_model::my_explore"]). The check name is a plain
        # identifier, so the trailing ":<name>" segment is unambiguous.
        dg.AssetCheckKey(dg.AssetKey(["my_model::my_explore"]), "freshness_check"),
        dg.AssetCheckKey(dg.AssetKey(["snowflake", "db:schema:table"]), "row_count"),
    ],
)
def test_asset_check_key_user_string_roundtrip(check_key: AssetCheckKey) -> None:
    assert AssetCheckKey.from_user_string(check_key.to_user_string()) == check_key


def test_asset_job_key_from_db_string_returns_none_for_non_matching() -> None:
    assert AssetJobKey.from_db_string('["a"]') is None
    assert AssetJobKey.from_db_string('{"asset_key": "[\\"a\\"]", "check_name": "b"}') is None
    assert AssetJobKey.from_db_string("random_stuff") is None


def test_asset_job_key_from_graphql_input() -> None:
    key = AssetJobKey.from_graphql_input({"jobName": "my_job"})
    assert key == AssetJobKey("my_job")


def test_invalid_db_strings() -> None:
    # note: AssetKey has a catch-all method for converting any string to an asset key,
    # so we're just making sure that that holds up and doesn't produce weird AssetCheckKeys
    assert entity_key_from_db_string("random_stuff") == dg.AssetKey("random_stuff")
    assert entity_key_from_db_string('{"asset_key": "[\\"a\\"]"}') == dg.AssetKey(
        ["asset_key", "a"]
    )
    assert entity_key_from_db_string(
        '{"asset_key": "[\\"a\\"]", "check_name": "b", "other": 1}'
    ) == dg.AssetKey(["asset_key", "a", "check_name", "b", "other", "1"])
