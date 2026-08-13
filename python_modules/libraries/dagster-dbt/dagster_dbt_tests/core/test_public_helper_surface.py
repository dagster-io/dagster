"""Tests for the public helpers exposed for `@dbt_assets` programmatic users.

The component surface has richer functionality than the raw `@dbt_assets`
decorator, but there's a lot users can get by wiring the helpers themselves.
These tests lock in the public re-exports so someone doesn't accidentally
break the import path or unmark them as `@public`.
"""

from pathlib import Path

import dagster as dg
import pytest


def test_dbt_defer_config_publicly_importable_from_dagster_dbt():
    """``DbtDeferConfig`` is a first-class public helper — programmatic users
    can construct one and call ``to_cli_args()`` to get the slim-CI flags.
    """
    from dagster_dbt import DbtDeferConfig

    config = DbtDeferConfig(state_path="/prod/state")
    assert config.to_cli_args() == ["--state", "/prod/state", "--defer"]


def test_dbt_defer_config_favor_state_flag():
    """`favor_state=True` appends the extra flag. Composes with `defer=True`."""
    from dagster_dbt import DbtDeferConfig

    config = DbtDeferConfig(state_path="/prod/state", favor_state=True)
    assert config.to_cli_args() == ["--state", "/prod/state", "--defer", "--favor-state"]


def test_apply_dbt_state_tags_publicly_importable():
    """``apply_dbt_state_tags`` is exposed for `@dbt_assets` users who want
    state-aware selection without adopting the component. Takes existing specs
    plus a state manifest path and returns tagged specs.
    """
    from dagster_dbt import apply_dbt_state_tags

    assert callable(apply_dbt_state_tags)


def test_apply_dbt_state_tags_end_to_end(tmp_path: Path):
    """Full round-trip: build specs + state manifest, call the public helper,
    verify the resulting specs carry the `dbt/state=modified|unchanged|new` tag.
    This mirrors what an `@dbt_assets` user would do.
    """
    import json

    from dagster_dbt import apply_dbt_state_tags

    current_manifest = {
        "nodes": {
            "model.my_project.my_model": {
                "resource_type": "model",
                "unique_id": "model.my_project.my_model",
                "name": "my_model",
                "checksum": {"name": "sha256", "checksum": "current-hash"},
            },
        }
    }
    state_manifest = {
        "nodes": {
            "model.my_project.my_model": {
                "resource_type": "model",
                "unique_id": "model.my_project.my_model",
                "name": "my_model",
                "checksum": {"name": "sha256", "checksum": "prod-hash"},  # different
            }
        }
    }
    state_path = tmp_path / "prod_state.json"
    state_path.write_text(json.dumps(state_manifest))

    specs = [
        dg.AssetSpec(
            key=dg.AssetKey("my_model"),
            metadata={"dagster_dbt/unique_id": "model.my_project.my_model"},
        )
    ]
    tagged = apply_dbt_state_tags(
        asset_specs=specs,
        current_manifest=current_manifest,
        state_manifest_path=state_path,
    )
    assert tagged[0].tags.get("dbt/state") == "modified"


def test_apply_dbt_state_tags_raises_on_missing_path(tmp_path: Path):
    """Missing state manifest path is a config error (not a silent no-op) — surfaces
    early so users don't ship a config that pretends to be doing state-aware
    selection but actually does nothing.
    """
    from dagster_dbt import apply_dbt_state_tags

    with pytest.raises(dg.DagsterInvalidDefinitionError):
        apply_dbt_state_tags(
            asset_specs=[],
            current_manifest={},
            state_manifest_path=tmp_path / "does_not_exist.json",
        )


def test_build_dbt_cloud_explorer_url_publicly_importable():
    """``build_dbt_cloud_explorer_url`` is exposed so programmatic Cloud users
    can attach Explorer URLs to their own specs (mirrors what `DbtCloudComponent`
    does via `enable_dbt_cloud_explorer_url`).
    """
    from dagster_dbt import build_dbt_cloud_explorer_url

    url = build_dbt_cloud_explorer_url(
        access_url="https://cloud.getdbt.com",
        account_id=1,
        project_id=2,
        environment_id=3,
        unique_id="model.pkg.my_model",
    )
    assert url == (
        "https://cloud.getdbt.com/explore/1/projects/2/environments/3/details/model.pkg.my_model"
    )
