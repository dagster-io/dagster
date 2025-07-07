# This file strictly contains tests for deprecation warnings. It can serve as a central record of
# deprecations for the current version.
import re

import dagster as dg
import pytest
from dagster._core.definitions.metadata import MetadataValue


def test_metadata_entry():
    with pytest.warns(DeprecationWarning, match=re.escape("MetadataEntry")):
        dg.MetadataEntry("foo", value=MetadataValue.text("bar"))


def test_schedule_environment_vars():
    with pytest.warns(DeprecationWarning, match=re.escape("environment_vars")):
        dg.ScheduleDefinition(
            name="foo",
            cron_schedule="@daily",
            job_name="bar",
            environment_vars={"foo": "bar"},
        )
