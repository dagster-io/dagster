import os
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest
from dagster_cloud_cli.core.pex_builder.package_manager import detect_package_manager
from dagster_cloud_cli.core.pex_builder.source import _build_local_package
from dagster_cloud_cli.ui import ExitWithMessage


@pytest.mark.integration
@pytest.mark.skipif(not shutil.which("uv"), reason="uv not installed")
class TestBuildLocalPackageUV:
    """Integration tests with real uv environments."""

    def test_build_with_uv_environment(self):
        """Create a uv venv without pip, verify local package builds successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create uv virtualenv (no pip)
            venv_path = Path(tmpdir) / "venv"
            # Use current python if 3.12 is not available
            subprocess.run(["uv", "venv", "--no-pip", str(venv_path)], check=True)

            if os.name == "nt":
                python_interp = str(venv_path / "Scripts" / "python.exe")
            else:
                python_interp = str(venv_path / "bin" / "python")

            # Create minimal local package
            pkg_dir = Path(tmpdir) / "local_pkg"
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(
                """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-pkg"
version = "0.1.0"
"""
            )
            (pkg_dir / "test_pkg.py").write_text("__version__ = '0.1.0'")

            # Test: Should detect uv and install successfully
            pm = detect_package_manager(python_interp)
            assert pm.name == "uv"

            target_dir = Path(tmpdir) / "target"
            cmd = pm.build_install_command(str(target_dir), python_interp)
            subprocess.run(cmd, check=True, cwd=pkg_dir)

            # Verify installation
            assert (target_dir / "test_pkg.py").exists()


@pytest.mark.integration
class TestBuildLocalPackagePip:
    """Integration tests with standard pip environments."""

    def test_build_with_pip_environment(self):
        """Verify pip environments continue to work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create standard virtualenv (has pip)
            venv_path = Path(tmpdir) / "venv"
            subprocess.run(["python", "-m", "venv", str(venv_path)], check=True)

            if os.name == "nt":
                python_interp = str(venv_path / "Scripts" / "python.exe")
                # Windows venv sometimes needs pip upgraded or installed
                subprocess.run(
                    [python_interp, "-m", "pip", "install", "--upgrade", "pip"], check=False
                )
            else:
                python_interp = str(venv_path / "bin" / "python")

            # Create minimal local package
            pkg_dir = Path(tmpdir) / "local_pkg"
            pkg_dir.mkdir()
            (pkg_dir / "pyproject.toml").write_text(
                """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-pkg"
version = "0.1.0"
"""
            )
            (pkg_dir / "test_pkg.py").write_text("__version__ = '0.1.0'")

            # Test: Should detect pip and install successfully
            pm = detect_package_manager(python_interp)
            assert pm.name == "pip"

            target_dir = Path(tmpdir) / "target"
            cmd = pm.build_install_command(str(target_dir), python_interp)
            subprocess.run(cmd, check=True, cwd=pkg_dir)

            # Verify installation
            assert (target_dir / "test_pkg.py").exists()

    def test_failed_build_captures_output(self):
        """Verify that failed builds capture and report stdout/stderr."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Setup: Create standard virtualenv (has pip)
            venv_path = Path(tmpdir) / "venv"
            subprocess.run(["python", "-m", "venv", str(venv_path)], check=True)

            if os.name == "nt":
                python_interp = str(venv_path / "Scripts" / "python.exe")
            else:
                python_interp = str(venv_path / "bin" / "python")

            # Ensure setuptools is available for setup.py build
            subprocess.run([python_interp, "-m", "pip", "install", "setuptools"], check=True)

            # Create a broken local package (invalid syntax in setup.py)
            pkg_dir = Path(tmpdir) / "broken_pkg"
            pkg_dir.mkdir()
            (pkg_dir / "setup.py").write_text(
                "import setuptools; raise Exception('Build failed manually!')"
            )

            with pytest.raises(ExitWithMessage) as exc_info:
                _build_local_package(str(pkg_dir), str(Path(tmpdir) / "build"), python_interp)

            error_msg = exc_info.value.message
            assert "Package installation failed" in error_msg
            assert "Build failed manually!" in error_msg
            assert "Stdout: " in error_msg
            assert "Stderr: " in error_msg
