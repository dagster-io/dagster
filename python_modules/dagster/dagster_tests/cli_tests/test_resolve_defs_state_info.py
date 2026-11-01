import logging
import os
import stat
from pathlib import Path

import pytest
from dagster._cli.utils import DEFS_STATE_INFO_OVERRIDE_PATH_ENV, resolve_serialized_defs_state_info
from dagster._utils.env import environ


@pytest.fixture
def logger():
    return logging.getLogger("test_resolve_defs_state_info")


def test_env_unset_returns_cli_arg(logger, monkeypatch):
    monkeypatch.delenv(DEFS_STATE_INFO_OVERRIDE_PATH_ENV, raising=False)
    assert resolve_serialized_defs_state_info("from-cli", logger) == "from-cli"
    assert resolve_serialized_defs_state_info(None, logger) is None


def test_env_set_file_nonempty_wins_over_cli(tmp_path: Path, logger):
    override = tmp_path / "defs_state_info"
    override.write_text("from-file")
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        assert resolve_serialized_defs_state_info("from-cli", logger) == "from-file"


def test_env_set_file_empty_means_no_pin(tmp_path: Path, logger):
    """An empty override file is an explicit 'no pin' — it must NOT fall back to
    the CLI arg, which may carry a stale pin from when the pod spec was created.
    """
    override = tmp_path / "defs_state_info"
    override.write_text("")
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        assert resolve_serialized_defs_state_info("from-cli", logger) is None


def test_env_set_file_whitespace_only_means_no_pin(tmp_path: Path, logger):
    override = tmp_path / "defs_state_info"
    override.write_text("   \n\t  \n")
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        assert resolve_serialized_defs_state_info("from-cli", logger) is None


def test_env_set_file_strips_whitespace(tmp_path: Path, logger):
    override = tmp_path / "defs_state_info"
    override.write_text("  from-file  \n")
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        assert resolve_serialized_defs_state_info("from-cli", logger) == "from-file"


def test_env_set_file_missing_falls_back(tmp_path: Path, logger):
    override = tmp_path / "does_not_exist"
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        assert resolve_serialized_defs_state_info("from-cli", logger) == "from-cli"
        assert resolve_serialized_defs_state_info(None, logger) is None


def test_env_set_file_unreadable_falls_back(tmp_path: Path, logger):
    override = tmp_path / "defs_state_info"
    override.write_text("from-file")
    os.chmod(override, 0)
    try:
        # Skip if running as root (chmod 0 wouldn't block read).
        if os.access(override, os.R_OK):
            pytest.skip("Running as root; cannot exercise permission denied path.")
        with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
            assert resolve_serialized_defs_state_info("from-cli", logger) == "from-cli"
    finally:
        os.chmod(override, stat.S_IRUSR | stat.S_IWUSR)


def test_env_set_and_cli_both_absent(tmp_path: Path, logger):
    override = tmp_path / "defs_state_info"
    override.write_text("from-file")
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        assert resolve_serialized_defs_state_info(None, logger) == "from-file"


def test_round_trip_with_serialized_defs_state_info(tmp_path: Path, logger):
    from dagster._serdes import deserialize_value, serialize_value
    from dagster_shared.serdes.objects.models.defs_state_info import DefsKeyStateInfo, DefsStateInfo

    info = DefsStateInfo(
        info_mapping={
            "key-a": DefsKeyStateInfo(version="v1", create_timestamp=1234567890.0),
        },
    )
    serialized = serialize_value(info)
    override = tmp_path / "defs_state_info"
    override.write_text(serialized)
    with environ({DEFS_STATE_INFO_OVERRIDE_PATH_ENV: str(override)}):
        resolved = resolve_serialized_defs_state_info(None, logger)
    assert resolved == serialized
    assert resolved is not None
    assert deserialize_value(resolved, DefsStateInfo) == info
