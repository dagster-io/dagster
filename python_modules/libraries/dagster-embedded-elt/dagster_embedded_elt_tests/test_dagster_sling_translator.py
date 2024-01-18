import pytest
from dagster import AssetKey, AutoMaterializePolicy, FreshnessPolicy, JsonMetadataValue
from dagster_embedded_elt.sling.dagster_sling_translator import DagsterSlingTranslator


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
def test_get_asset_key(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_asset_key(stream) == AssetKey.from_user_string(expected)


def test_get_asset_key_error():
    stream_definition = {"name": "foo", "config": {"meta": {"dagster": {"asset_key": "foo$bar"}}}}
    translator = DagsterSlingTranslator()
    with pytest.raises(ValueError):
        translator.get_asset_key(stream_definition)


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
def test_get_deps_asset_key(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_deps_asset_key(stream) == [AssetKey.from_user_string(e) for e in expected]


def test_get_deps_asset_key_error():
    stream_definition = {"name": "foo", "config": {"meta": {"dagster": {"deps": "foo$bar"}}}}
    translator = DagsterSlingTranslator()
    with pytest.raises(ValueError):
        translator.get_deps_asset_key(stream_definition)


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
def test_get_description(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_description(stream) == expected


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
def test_get_metadata(stream, expected):
    translator = DagsterSlingTranslator()
    stream = {"name": "foo", "config": {"foo": "bar"}}
    assert translator.get_metadata(stream) == {"stream_config": JsonMetadataValue(stream["config"])}


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        (
            {"name": "foo", "config": {"meta": {"dagster": {"group": "foo.bar"}}}},
            "foo.bar",
        ),
    ],
)
def test_get_group_name(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_group_name(stream) == expected


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        (
            {
                "name": "foo",
                "config": {"meta": {"dagster": {"freshness_policy": {"maximum_lag_minutes": 5}}}},
            },
            FreshnessPolicy(maximum_lag_minutes=5),
        ),
    ],
)
def test_get_freshness_policy(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_freshness_policy(stream) == expected


@pytest.mark.parametrize(
    "stream,expected",
    [
        ({"name": "foo"}, None),
        (
            {
                "name": "foo",
                "config": {"meta": {"dagster": {"auto_materialize_policy": {"type": "eager"}}}},
            },
            AutoMaterializePolicy.eager(),
        ),
        (
            {
                "name": "foo",
                "config": {"meta": {"dagster": {"auto_materialize_policy": {"type": "lazy"}}}},
            },
            AutoMaterializePolicy.lazy(),
        ),
    ],
)
def test_get_auto_materialize_policy(stream, expected):
    translator = DagsterSlingTranslator()
    assert translator.get_auto_materialize_policy(stream) == expected
