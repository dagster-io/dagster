import shutil
import subprocess
from typing import Literal

from dagster_shared.record import record


class PackageManagerError(Exception):
    """Raised when no suitable package manager is found."""


@record(kw_only=False)
class PackageManager:
    name: Literal["pip", "uv"]
    executable: str

    def build_install_command(
        self, target_dir: str, python_interpreter: str, no_deps: bool = True
    ) -> list[str]:
        """Construct full install command for local package."""
        if self.name == "pip":
            cmd = [self.executable, "-m", "pip", "install", "--target", target_dir]
        else:  # uv
            cmd = [
                self.executable,
                "pip",
                "install",
                "--target",
                target_dir,
                "--python",
                python_interpreter,
            ]

        if no_deps:
            cmd.append("--no-deps")
        cmd.append(".")  # Current directory (local package)
        return cmd


def detect_package_manager(python_interpreter: str) -> PackageManager:
    """Detect available package manager for the given interpreter.

    Strategy:
    1. Check if pip is importable in the interpreter (preferred for compatibility)
    2. If no pip, check for uv availability
    3. Raise clear error if neither available
    """
    # Test 1: Can we import pip in this interpreter?
    pip_test = subprocess.run(
        [python_interpreter, "-c", "import pip; print(pip.__version__)"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    if pip_test.returncode == 0:
        return PackageManager(
            name="pip",
            executable=python_interpreter,
        )

    # Test 2: Is uv available in PATH?
    uv_path = shutil.which("uv")
    if uv_path:
        # Verify uv supports pip subcommand
        uv_test = subprocess.run(
            [uv_path, "pip", "--help"],
            capture_output=True,
            timeout=30,
            check=False,
        )
        if uv_test.returncode == 0:
            return PackageManager(
                name="uv",
                executable=uv_path,
            )

    # Failure: Neither available
    raise PackageManagerError(
        f"No package manager available for interpreter: {python_interpreter}\n"
        f"Pip check failed: {pip_test.stderr.strip()}\n"
        f"Uv availability: {'found but pip subcommand failed' if uv_path else 'not found'}\n"
        "Please ensure either pip is installed in your environment or uv is available."
    )
