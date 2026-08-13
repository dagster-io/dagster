"""Tests for the ``defer_config`` component field that appends dbt's
``--state``/``--defer``/``--favor-state`` flags to CLI invocations.

Enables the slim CI / defer-to-prod-state pattern without asking users to edit
`cli_args` manually. The state path is user-provided (Dagster doesn't generate it);
composes cleanly with ``state_manifest_path`` when pointing at the same file.
"""

from dagster_dbt.components.dbt_project.component import DbtDeferConfig


def test_defer_config_defaults_to_defer_flag() -> None:
    config = DbtDeferConfig(state_path="/prod_state")
    assert config.to_cli_args() == ["--state", "/prod_state", "--defer"]


def test_defer_config_defer_false() -> None:
    # Some users want just `--state <path>` without `--defer` (e.g., for `dbt clone` or
    # per-run selection with `state:modified` outside of Dagster).
    config = DbtDeferConfig(state_path="/prod_state", defer=False)
    assert config.to_cli_args() == ["--state", "/prod_state"]


def test_defer_config_with_favor_state() -> None:
    config = DbtDeferConfig(state_path="/prod_state", favor_state=True)
    assert config.to_cli_args() == ["--state", "/prod_state", "--defer", "--favor-state"]


def test_defer_config_favor_state_without_defer() -> None:
    config = DbtDeferConfig(state_path="/prod_state", defer=False, favor_state=True)
    assert config.to_cli_args() == ["--state", "/prod_state", "--favor-state"]


def test_defer_config_state_path_preserved_as_given() -> None:
    # The state_path is passed through verbatim — users control absolute vs relative,
    # trailing slashes, `manifest.json` vs directory-containing-manifest, etc. dbt
    # itself does the right thing for each form.
    for path in ("/abs/prod", "relative/prod", "/prod/manifest.json"):
        assert DbtDeferConfig(state_path=path).to_cli_args()[1] == path
