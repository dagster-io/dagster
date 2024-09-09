from typing import Any, Mapping

import pytest
from dagster_dbt.asset_utils import default_tags_from_dbt_resource_props


@pytest.mark.parametrize(
    "dbt_resource_props,tags",
    [
        ({}, {}),
        ({"tags": ["tag"]}, {"tag": ""}),
        ({"random_key": ["tag"]}, {}),
        ({"tags": ["tag=invalid"]}, {}),
        ({"tags": ["tag1", "tag2"]}, {"tag1": "", "tag2": ""}),
        ({"tags": ["tag1", "tag2", "tag=invalid"]}, {"tag1": "", "tag2": ""}),
        ({"tags": ["tag1", "tag1"]}, {"tag1": ""}),
    ],
)
def test_default_tags_from_dbt_resource_props(
    dbt_resource_props: Mapping[str, Any], tags: Mapping[str, str]
) -> None:
    assert default_tags_from_dbt_resource_props(dbt_resource_props) == tags
