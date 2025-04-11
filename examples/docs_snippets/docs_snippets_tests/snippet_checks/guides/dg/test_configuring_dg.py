from pathlib import Path

from dagster_dg.config import load_dg_root_file_config, load_dg_user_file_config

from docs_snippets_tests.snippet_checks.guides.components.utils import (
    DAGSTER_ROOT,
    EDITABLE_DIR,
    format_multiline,
    isolated_snippet_generation_environment,
)
from docs_snippets_tests.snippet_checks.utils import (
    _run_command,
    check_file,
    compare_tree_output,
    create_file,
    re_ignore_after,
    re_ignore_before,
    run_command_and_snippet_output,
)

SNIPPETS_DIR = (
    DAGSTER_ROOT
    / "examples"
    / "docs_snippets"
    / "docs_snippets"
    / "guides"
    / "dg"
    / "configuring-dg"
)


def test_user_config_valid():
    toml_path = SNIPPETS_DIR / "user-config.toml"
    load_dg_user_file_config(toml_path)


def test_workspace_config_valid():
    toml_path = SNIPPETS_DIR / "workspace-config.toml"
    load_dg_root_file_config(toml_path, config_format="root")


def test_project_config_valid():
    toml_path = SNIPPETS_DIR / "project-config.toml"
    load_dg_root_file_config(toml_path)
