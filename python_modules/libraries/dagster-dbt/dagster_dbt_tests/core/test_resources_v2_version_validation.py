import pytest
from dagster_dbt.core.resources_v2 import DbtCliResource
from dbt.version import __version__ as dbt_version
from packaging import version
from pydantic import ValidationError

from ..conftest import TEST_PROJECT_DIR


@pytest.mark.skipif(
    version.parse(dbt_version) >= version.parse("1.4.0"),
    reason="Validates invalid dbt core versions only",
)
def test_resource_requires_minimum_dbt_version() -> None:
    with pytest.raises(ValidationError):
        DbtCliResource(project_dir=TEST_PROJECT_DIR)
