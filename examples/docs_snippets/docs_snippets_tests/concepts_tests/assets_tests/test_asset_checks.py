import pytest

from docs_snippets.concepts.assets.asset_checks.asset_with_check import (
    defs as asset_with_check_defs,
)
from docs_snippets.concepts.assets.asset_checks.metadata import defs as metadata_defs
from docs_snippets.concepts.assets.asset_checks.orders_check import defs as orders_defs
from docs_snippets.concepts.assets.asset_checks.severity import defs as severity_defs


@pytest.mark.parametrize(
    "defs", [orders_defs, asset_with_check_defs, severity_defs, metadata_defs]
)
def test_execute(defs):
    job_def = defs.get_implicit_global_asset_job_def()
    result = job_def.execute_in_process()
    assert result.success
