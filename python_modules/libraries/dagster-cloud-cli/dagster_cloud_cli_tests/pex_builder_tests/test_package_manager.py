import os
import subprocess
import tempfile
from unittest.mock import MagicMock, patch

import pytest
from dagster_cloud_cli.core.pex_builder.package_manager import (
    PackageManager,
    PackageManagerError,
    detect_package_manager,
)
from dagster_cloud_cli.core.pex_builder.source import _build_local_package
from dagster_cloud_cli.ui import ExitWithMessage


class TestDetectPackageManager:
    """Test package manager detection logic."""

    def test_prefers_pip_when_available(self):
        """Should return pip manager when pip is importable."""
        with patch("subprocess.run") as mock_run:
            # Mock successful pip check
            mock_run.return_value = MagicMock(returncode=0, stdout="24.0", stderr="")

            pm = detect_package_manager("/usr/bin/python3")
            assert pm.name == "pip"
            assert pm.executable == "/usr/bin/python3"

    def test_falls_back_to_uv_when_pip_missing(self):
        """Should return uv manager when pip fails but uv available."""
        with patch("subprocess.run") as mock_run, patch("shutil.which") as mock_which:
            # First call (pip check) fails, second (uv check) succeeds
            mock_run.side_effect = [
                MagicMock(returncode=1, stderr="No module named pip"),  # pip check
                MagicMock(returncode=0),  # uv pip --help check
            ]
            mock_which.return_value = "/usr/bin/uv"

            pm = detect_package_manager("/path/to/python")
            assert pm.name == "uv"
            assert pm.executable == "/usr/bin/uv"

    def test_raises_error_when_neither_available(self):
        """Should raise PackageManagerError when no manager found."""
        with patch("subprocess.run") as mock_run, patch("shutil.which") as mock_which:
            mock_run.return_value = MagicMock(returncode=1, stderr="No module named pip")
            mock_which.return_value = None

            with pytest.raises(PackageManagerError) as exc_info:
                detect_package_manager("/path/to/python")

            assert "No package manager available" in str(exc_info.value)

    def test_uv_pip_subcommand_validation(self):
        """Should verify uv supports pip subcommand."""
        with patch("subprocess.run") as mock_run, patch("shutil.which") as mock_which:
            mock_run.side_effect = [
                MagicMock(returncode=1),  # pip fails
                MagicMock(returncode=1, stderr="unknown command"),  # uv pip fails
            ]
            mock_which.return_value = "/usr/bin/uv"

            with pytest.raises(PackageManagerError):
                detect_package_manager("/path/to/python")


class TestPackageManagerCommands:
    """Test command construction."""

    def test_pip_command_structure(self):
        pm = PackageManager("pip", "/usr/bin/python3")
        cmd = pm.build_install_command("/tmp/target", "/usr/bin/python3")
        assert cmd[0] == "/usr/bin/python3"
        assert "-m" in cmd
        assert "pip" in cmd
        assert "--target" in cmd
        assert "/tmp/target" in cmd
        assert "--no-deps" in cmd
        assert "." in cmd

    def test_uv_command_structure(self):
        pm = PackageManager("uv", "/usr/bin/uv")
        cmd = pm.build_install_command("/tmp/target", "/usr/bin/python3")
        assert cmd[0] == "/usr/bin/uv"
        assert "pip" in cmd
        assert "--python" in cmd
        assert "/usr/bin/python3" in cmd
        assert "--target" in cmd

    def test_error_handler_attribute_error_regression(self):
        """P1: Verify the error handler is safe when stderr is None but stdout has content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a dummy pyproject.toml to hit the relevant code path
            with open(os.path.join(temp_dir, "pyproject.toml"), "w") as f:
                f.write("[project]\nname='test'")

            with (
                patch(
                    "dagster_cloud_cli.core.pex_builder.source.detect_package_manager"
                ) as mock_detect,
                patch("subprocess.run") as mock_run,
            ):
                mock_detect.return_value = PackageManager("pip", "python")

                # Simulate CalledProcessError where stdout exists but stderr is None
                # This could happen if capture_output=False (legacy) or if mocked incorrectly
                error = subprocess.CalledProcessError(returncode=1, cmd=["pip", "install"])
                error.stdout = "some stdout content"
                error.stderr = None

                mock_run.side_effect = error

                with pytest.raises(ExitWithMessage) as exc_info:
                    _build_local_package(temp_dir, "/tmp/build", "python")

                # The fix ensures we don't raise AttributeError: 'NoneType' object has no attribute 'decode'
                # and instead include the stdout content correctly.
                assert "Package installation failed" in exc_info.value.message
                assert "Stdout: some stdout content" in exc_info.value.message
                assert "Stderr: " in exc_info.value.message
