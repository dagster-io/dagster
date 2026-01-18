import pytest
from dagster import AssetKey, AutoMaterializePolicy, JsonMetadataValue
from dagster_sling.dagster_sling_translator import DagsterSlingTranslator


@pytest.mark.parametrize(
    "test,expected",
    [
        ("foo", "foo"),
        ("foo.bar", "foo.bar"),
        ("foo.$bar$", "foo._bar_"),
    ],
)
def test_sling_translator_sanitize(test, expected):
    translator = DagsterSlingTranslator()

    assert translator.sanitize_stream_name(test) == expected


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, "target/foo"),
        ({"name": "public.foo"}, "target/public/foo"),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"asset_key": "foo.bar"}}}},
            "foo/bar",
        ),
    ],
)
def test_asset_key_from_get_asset_spec(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_asset_spec(stream).key == AssetKey.from_user_string(expected)


def test_asset_key_from_get_asset_spec_error():
    stream_definition = {"name": "foo", "config": {"meta": {"dagster": {"asset_key": "foo$bar"}}}}
    translator = DagsterSlingTranslator()
    with pytest.raises(ValueError):
        translator.get_asset_spec(stream_definition).key  # noqa


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, ["foo"]),
        ({"name": "public.foo"}, ["public/foo"]),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"deps": "foo.bar"}}}},
            ["foo/bar"],
        ),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"deps": ["foo_one", "foo_two"]}}}},
            ["foo_one", "foo_two"],
        ),
    ],
)
def test_deps_asset_key_from_get_asset_spec(stream, expected):
    translator = DagsterSlingTranslator()
    assert [dep.asset_key for dep in translator.get_asset_spec(stream).deps] == [
        AssetKey.from_user_string(e) for e in expected
    ]


def test_deps_asset_key_from_get_asset_spec_error():
    stream_definition = {"name": "foo", "config": {"meta": {"dagster": {"deps": "foo$bar"}}}}
    translator = DagsterSlingTranslator()
    with pytest.raises(ValueError):
        translator.get_asset_spec(stream_definition).deps  # noqa


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        ({"name": "public.foo"}, None),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"description": "foo.bar"}}}},
            "foo.bar",
        ),
    ],
)
def test_description_from_get_asset_spec(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_asset_spec(stream).description == expected


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"description": "foo.bar"}}}},
            "foo.bar",
        ),
    ],
)
def test_metadata_from_get_asset_spec(stream, expected):
    translator = DagsterSlingTranslator()
    stream = {"name": "foo", "config": {"foo": "bar"}}
    assert translator.get_asset_spec(stream).metadata == {
        "stream_config": JsonMetadataValue(stream["config"])
    }


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"group": "foo_bar"}}}},
            "foo_bar",
        ),
    ],
)
def test_group_name_from_get_asset_spec(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_asset_spec(stream).group_name == expected


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        (
            {
                "name": "foo",
                "config": {"meta": {"dagster": {"auto_materialize_policy": {}}}},
            },
            AutoMaterializePolicy.eager(),
        ),
    ],
)
def test_auto_materialize_policy_from_get_asset_spec(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_asset_spec(stream).auto_materialize_policy == expected
