"""Test fixtures for dagster-airflow.

These make very heavy use of fixture dependency and scope. If you're unfamiliar with pytest
fixtures, read: https://docs.pytest.org/en/latest/fixture.html.
"""
import os

IS_BUILDKITE = os.getenv("BUILDKITE") is not None
