from typing import Sequence

import pytest
from dagster import AssetSelection, AssetSpec, JobDefinition, asset, job, multi_asset


def test_asset_decorator_string_tags():
    @asset(tags={"foo", "bar=barval"})
    def asset1():
        ...

    assert asset1.tags == {"foo": None, "bar": "barval"}
    assert asset1.tag_strings == {"foo", "bar=barval"}


def test_asset_decorator_dict_tags():
    @asset(tags={"foo": "fooval", "bar": None})
    def asset1():
        ...

    assert asset1.tags == {"foo": "fooval", "bar": None}
    assert asset1.tag_strings == {"foo=fooval", "bar"}


def test_asset_spec_string_tags():
    asset1_spec = AssetSpec("asset1", tags={"foo", "bar=barval"})
    assert asset1_spec.tags == {"foo": None, "bar": "barval"}
    assert asset1_spec.tag_strings == {"foo", "bar=barval"}

    @multi_asset(specs=[asset1_spec])
    def assets():
        ...

    assert assets.tags_by_key[asset1_spec.key] == {"foo": None, "bar": "barval"}
    assert assets.tag_strings_by_key[asset1_spec.key] == {"foo", "bar=barval"}


def test_asset_spec_dict_tags():
    asset1_spec = AssetSpec("asset1", tags={"foo": "fooval", "bar": None})
    assert asset1_spec.tags == {"foo": None, "bar": "barval"}
    assert asset1_spec.tag_strings == {"foo", "bar=barval"}

    @multi_asset(specs=[asset1_spec])
    def assets():
        ...

    assert assets.tags_by_key[asset1_spec.key] == {"foo": None, "bar": "barval"}
    assert assets.tag_strings_by_key[asset1_spec.key] == {"foo", "bar=barval"}


def test_key_conflict():
    with pytest.raises:

        @asset(tags={"foo", "foo=bar"})
        def asset1():
            ...


def test_equals_in_key():
    with pytest.raises:

        @asset(tags={"foo=bar": "baz"})
        def asset1():
            ...


def test_tag_selection():
    @multi_asset(
        specs=[
            AssetSpec("asset1", tags={"foo"}),
            AssetSpec("asset2", tags={"foo", "somethingelse"}),
            AssetSpec("asset3", tags={"bar"}),
            AssetSpec("asset3", tags={"foo", "bar"}),
            AssetSpec("asset4", tags={"baz=bazval", "somethingelse"}),
            AssetSpec("asset5", tags={"foo=fooval"}),
        ]
    )
    def assets():
        ...

    assert AssetSelection.tag_string("foo").resolve([assets]) == {"asset1", "asset2"}
    assert AssetSelection.tag_string("foo=bazval").resolve([assets]) == {"asset4"}
    assert AssetSelection.tag(key="foo", value="bar").resolve([assets]) == {"asset3"}
    assert AssetSelection.tag(key="foo", value=None).resolve([assets]) == {"asset1", "asset2"}


def get_jobs_with_tag_string(
    jobs: Sequence[JobDefinition], tag_string: str
) -> Sequence[JobDefinition]:
    """Returns jobs that have a tag that matches the given tag string."""
    result = []
    for job_def in jobs:
        for tag_key, tag_value in job_def.items():
            if tag_value is None:
                if tag_key == tag_string:
                    result.append(job_def)
            elif f"{tag_key}={tag_value}" == tag_string:
                result.append(job_def)

    return result


def test_job_decorator_string_tags_equals_in_key():
    """This test demonstrates some gnarliness that arises by giving '=' special meaning, even
    though it's not a reserved character in job tags for historical reasons.
    """
    with pytest.raises(match="Can't use '=' in tag keys with None value"):

        @job(tags={"foo=x": None})
        def job0():
            ...

    with pytest.warns(match="Using '=' in tag keys is deprecated"):

        @job(tags={"foo=x": "bar"})
        def job1():
            ...

    @job(tags={"foo": "x=bar"})
    def job2():
        ...

    # Even though the jobs have different tags when viewed in dictionary form, they both match the
    # same tag string "foo=x=bar"
    assert get_jobs_with_tag_string([job1, job2], "foo=x=bar") == [job1, job2]
