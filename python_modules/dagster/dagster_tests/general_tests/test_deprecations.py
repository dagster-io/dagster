# This file strictly contains tests for deprecation warnings. It can serve as a central record of
# deprecations for the current version.

import re

import pytest
from dagster._core.definitions.metadata import MetadataEntry, MetadataValue
from dagster._core.definitions.schedule_definition import ScheduleDefinition


def test_metadata_entry():
    with pytest.warns(DeprecationWarning, match=re.escape("MetadataEntry")):
        MetadataEntry("foo", value=MetadataValue.text("bar"))


def test_schedule_environment_vars():
    with pytest.warns(DeprecationWarning, match=re.escape("environment_vars")):
        ScheduleDefinition(
            name="foo",
            cron_schedule="@daily",
            job_name="bar",
            environment_vars={"foo": "bar"},
        )
