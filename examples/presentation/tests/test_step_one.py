import pytest

from dagster import seven

from ..step_one import compute_top_quartile


@pytest.mark.skipif(seven.IS_WINDOWS, reason="Unix-only test")
def test_top_quartile(snapshot):
    snapshot.assert_match(compute_top_quartile())
