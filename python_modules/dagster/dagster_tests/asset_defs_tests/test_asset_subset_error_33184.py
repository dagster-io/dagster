"""Tests for DagsterInvalidSubsetError diagnostic info and asset selection resolution.

Reproduces issue #33184: DagsterInvalidSubsetError for an asset that exists when
materializing from the UI via get_subset().
"""

import re

import dagster as dg
import pytest
from dagster._core.definitions.assets.job.asset_job import IMPLICIT_ASSET_JOB_NAME
from dagster._core.errors import DagsterInvalidSubsetError


def test_materialize_asset_with_key_prefix_via_get_subset():
    """Reproduces the flow when a user clicks 'Materialize' on a single asset in the UI.

    The UI flow calls: get_maybe_subset_job_def() → get_subset(asset_selection={key})
    → _get_job_def_for_asset_selection() → get_asset_graph_for_job()
    → selection.resolve() → KeysAssetSelection.resolve_inner()

    This test ensures an asset with key_prefix="dbt" can be successfully materialized
    via the get_subset path, which is the exact flow from issue #33184.
    """

    @dg.asset(key_prefix="dbt")
    def freeze_raw_data():
        return 1

    defs = dg.Definitions(assets=[freeze_raw_data])
    repo_def = defs.get_repository_def()

    # This is the exact path the UI takes when clicking "Materialize"
    implicit_job = repo_def.get_job(IMPLICIT_ASSET_JOB_NAME)

    # The user selects a single asset to materialize
    asset_key = dg.AssetKey(["dbt", "freeze_raw_data"])

    # This should NOT raise DagsterInvalidSubsetError
    subset_job = implicit_job.get_subset(asset_selection={asset_key})
    assert subset_job is not None
    assert subset_job.name == IMPLICIT_ASSET_JOB_NAME


def test_materialize_multiple_assets_with_key_prefix_via_get_subset():
    """Tests materializing multiple assets with key_prefix via get_subset."""

    @dg.asset(key_prefix="dbt")
    def asset_a():
        return 1

    @dg.asset(key_prefix="dbt")
    def asset_b():
        return 2

    @dg.asset
    def asset_c():
        return 3

    defs = dg.Definitions(assets=[asset_a, asset_b, asset_c])
    repo_def = defs.get_repository_def()
    implicit_job = repo_def.get_job(IMPLICIT_ASSET_JOB_NAME)

    # Materialize just the dbt-prefixed assets
    subset_job = implicit_job.get_subset(
        asset_selection={
            dg.AssetKey(["dbt", "asset_a"]),
            dg.AssetKey(["dbt", "asset_b"]),
        }
    )
    assert subset_job is not None


def test_error_message_includes_diagnostic_info():
    """Tests that DagsterInvalidSubsetError includes diagnostic info about the asset graph."""

    @dg.asset
    def my_asset():
        return 1

    defs = dg.Definitions(assets=[my_asset])
    repo_def = defs.get_repository_def()
    implicit_job = repo_def.get_job(IMPLICIT_ASSET_JOB_NAME)

    # Try to materialize a non-existent asset
    with pytest.raises(DagsterInvalidSubsetError, match=r"Diagnostic info"):
        implicit_job.get_subset(asset_selection={dg.AssetKey(["nonexistent_asset"])})


def test_error_message_includes_key_counts():
    """Tests that the diagnostic info includes total and materializable key counts."""

    @dg.asset
    def existing_asset():
        return 1

    @dg.asset
    def another_asset():
        return 2

    defs = dg.Definitions(assets=[existing_asset, another_asset])
    repo_def = defs.get_repository_def()
    implicit_job = repo_def.get_job(IMPLICIT_ASSET_JOB_NAME)

    with pytest.raises(
        DagsterInvalidSubsetError,
        match=re.compile(r"Diagnostic info.*total keys.*materializable keys", re.DOTALL),
    ):
        implicit_job.get_subset(asset_selection={dg.AssetKey(["does_not_exist"])})


def test_get_subset_via_repository_get_maybe_subset_job_def():
    """Tests the exact code path from ReconstructableJob.get_definition(), which calls
    RepositoryDefinition.get_maybe_subset_job_def().
    """

    @dg.asset(key_prefix="dbt")
    def freeze_raw_data():
        return 1

    @dg.asset
    def downstream(freeze_raw_data):
        return freeze_raw_data + 1

    defs = dg.Definitions(assets=[freeze_raw_data, downstream])
    repo_def = defs.get_repository_def()

    asset_key = dg.AssetKey(["dbt", "freeze_raw_data"])

    # This is the exact method called in the reconstruction path
    subset_job = repo_def.get_maybe_subset_job_def(
        IMPLICIT_ASSET_JOB_NAME,
        asset_selection={asset_key},
    )
    assert subset_job is not None
