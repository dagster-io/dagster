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
from dagster_cloud_cli.core.pex_builder.source import _build_local_package, build_pex_using_setup_py
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

            def which_side_effect(name):
                if name == "uv":
                    return "/usr/bin/uv"
                return name  # passthrough for interpreter normalization

            mock_which.side_effect = which_side_effect

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

            def which_side_effect(name):
                if name == "uv":
                    return "/usr/bin/uv"
                return name  # passthrough for interpreter normalization

            mock_which.side_effect = which_side_effect

            with pytest.raises(PackageManagerError):
                detect_package_manager("/path/to/python")


class TestPackageManagerCommands:
    """Test command construction."""

    def test_pip_command_structure(self):
        pm = PackageManager("pip", "/usr/bin/python3", "/usr/bin/python3")
        cmd = pm.build_install_command("/tmp/target")
        assert cmd[0] == "/usr/bin/python3"
        assert "-m" in cmd
        assert "pip" in cmd
        assert "--target" in cmd
        assert "/tmp/target" in cmd
        assert "--no-deps" in cmd
        assert "." in cmd

    def test_uv_command_structure(self):
        pm = PackageManager("uv", "/usr/bin/uv", "/usr/bin/python3")
        cmd = pm.build_install_command("/tmp/target")
        assert cmd[0] == "/usr/bin/uv"
        assert "pip" in cmd
        assert "--python" in cmd
        assert "/usr/bin/python3" in cmd  # uses pm.python_interpreter, not caller-supplied path
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
                mock_detect.return_value = PackageManager("pip", "python", "python")

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


class TestBuildPexUsingSetupPy:
    """Test lazy package manager detection in build_pex_using_setup_py."""

    def test_detect_called_once_for_multiple_pyproject_packages(self):
        """detect_package_manager should be called exactly once even for multiple pyproject packages."""
        with (
            tempfile.TemporaryDirectory() as code_dir,
            tempfile.TemporaryDirectory() as dep1_dir,
            tempfile.TemporaryDirectory() as dep2_dir,
        ):
            # All three dirs have pyproject.toml
            for d in (code_dir, dep1_dir, dep2_dir):
                with open(os.path.join(d, "pyproject.toml"), "w") as f:
                    f.write("[project]\nname='test'")

            fake_pm = PackageManager("pip", "python", "python")

            with (
                patch(
                    "dagster_cloud_cli.core.pex_builder.source.detect_package_manager"
                ) as mock_detect,
                patch(
                    "dagster_cloud_cli.core.pex_builder.source._build_local_package"
                ) as mock_build,
                patch(
                    "dagster_cloud_cli.core.pex_builder.util.python_interpreter_for"
                ) as mock_interp,
                patch("dagster_cloud_cli.core.pex_builder.source._prepare_working_directory"),
                patch("dagster_cloud_cli.core.pex_builder.util.get_pex_flags") as mock_pex_flags,
                patch("dagster_cloud_cli.core.pex_builder.util.build_pex") as mock_build_pex,
            ):
                mock_detect.return_value = fake_pm
                mock_interp.return_value = "/usr/bin/python3"
                mock_pex_flags.return_value = []
                mock_build_pex.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

                build_pex_using_setup_py(code_dir, [dep1_dir, dep2_dir], "/tmp/out.pex", (3, 10))

                # Detection should happen exactly once, not once per package
                assert mock_detect.call_count == 1

                # Verify the detected pm was forwarded to all _build_local_package calls
                for call in mock_build.call_args_list:
                    assert call.kwargs.get("pm") is mock_detect.return_value

    def test_detect_not_called_for_setup_py_only_projects(self):
        """detect_package_manager should never be called when all packages use setup.py."""
        with (
            tempfile.TemporaryDirectory() as code_dir,
            tempfile.TemporaryDirectory() as dep1_dir,
        ):
            # Both dirs have only setup.py, no pyproject.toml
            for d in (code_dir, dep1_dir):
                with open(os.path.join(d, "setup.py"), "w") as f:
                    f.write("from setuptools import setup\nsetup(name='test')")

            with (
                patch(
                    "dagster_cloud_cli.core.pex_builder.source.detect_package_manager"
                ) as mock_detect,
                patch(
                    "dagster_cloud_cli.core.pex_builder.source._build_local_package"
                ) as mock_build,
                patch(
                    "dagster_cloud_cli.core.pex_builder.util.python_interpreter_for"
                ) as mock_interp,
                patch("dagster_cloud_cli.core.pex_builder.source._prepare_working_directory"),
                patch("dagster_cloud_cli.core.pex_builder.util.get_pex_flags") as mock_pex_flags,
                patch("dagster_cloud_cli.core.pex_builder.util.build_pex") as mock_build_pex,
            ):
                mock_interp.return_value = "/usr/bin/python3"
                mock_pex_flags.return_value = []
                mock_build_pex.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

                build_pex_using_setup_py(code_dir, [dep1_dir], "/tmp/out.pex", (3, 10))

                # Detection should never be called for setup.py-only projects
                assert mock_detect.call_count == 0
                assert mock_build.call_count == 2  # called once for dep1_dir, once for code_dir

    def test_detect_not_called_for_dual_manifest_packages(self):
        """detect_package_manager should not be called when all pyproject.toml dirs also have setup.py.

        setup.py always wins in _build_local_package, so a co-located pyproject.toml never
        triggers the pm code path and does not need a manager to be detected upfront.
        """
        with (
            tempfile.TemporaryDirectory() as code_dir,
            tempfile.TemporaryDirectory() as dep1_dir,
        ):
            # Both dirs have BOTH setup.py and pyproject.toml — setup.py should win
            for d in (code_dir, dep1_dir):
                with open(os.path.join(d, "setup.py"), "w") as f:
                    f.write("from setuptools import setup\nsetup(name='test')")
                with open(os.path.join(d, "pyproject.toml"), "w") as f:
                    f.write("[project]\nname='test'")

            with (
                patch(
                    "dagster_cloud_cli.core.pex_builder.source.detect_package_manager"
                ) as mock_detect,
                patch(
                    "dagster_cloud_cli.core.pex_builder.source._build_local_package"
                ) as mock_build,
                patch(
                    "dagster_cloud_cli.core.pex_builder.util.python_interpreter_for"
                ) as mock_interp,
                patch("dagster_cloud_cli.core.pex_builder.source._prepare_working_directory"),
                patch("dagster_cloud_cli.core.pex_builder.util.get_pex_flags") as mock_pex_flags,
                patch("dagster_cloud_cli.core.pex_builder.util.build_pex") as mock_build_pex,
            ):
                mock_interp.return_value = "/usr/bin/python3"
                mock_pex_flags.return_value = []
                mock_build_pex.return_value = MagicMock(returncode=0, stdout=b"", stderr=b"")

                build_pex_using_setup_py(code_dir, [dep1_dir], "/tmp/out.pex", (3, 10))

                # Detection should NOT be called: pyproject.toml dirs all have co-located setup.py
                assert mock_detect.call_count == 0
                assert mock_build.call_count == 2
