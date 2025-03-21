import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_venv():
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_venv = Path(temp_dir) / "venv"
        try:
            # Check if uv is installed
            subprocess.run(["uv", "--version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            raise Exception("uv is not installed or not in PATH")

        # Create a new virtual environment using uv
        result = subprocess.run(
            ["uv", "venv", temp_dir_venv, "--seed"], check=True, capture_output=True, text=True
        )
        assert result.returncode == 0, f"Failed to create virtual environment: {result.stderr}"

        # Verify the environment was created by checking if python executable exists
        python_executable = temp_dir_venv / "bin" / "python"
        assert python_executable.exists(), f"Python executable not found at {python_executable}"
        # Install uv
        uv_install_output = subprocess.run(
            [python_executable, "-m", "pip", "install", "uv"],
            check=True,
            capture_output=True,
            text=True,
        )
        assert (
            uv_install_output.returncode == 0
        ), f"Failed to install uv: {uv_install_output.stderr}"
        yield temp_dir_venv


def test_in_airflow_package_implicit_requirements(temp_venv: Path):
    """The dagster-airlift[in-airflow] package has an implicit dependency on Airflow, and should be able to work without dagster installed.
    This test news up a fresh virtualenv, installs the dagster-airlift[in-airflow] package, and ensures the following:
    - import dagster fails
    - import dagster_airlift.in_airflow fails with an error message indicating that Airflow is not installed
    Then, we install Airflow properly and run a separate import script to ensure that the package works as expected, and does not require dagster to be installed.
    """
    path_to_package = Path(__file__).parent.parent.parent.parent
    # install package using uv pip install
    python_executable = temp_venv / "bin" / "python"
    uv_entrypoint = [python_executable, "-m", "uv"]
    install_result = subprocess.run(
        [*uv_entrypoint, "pip", "install", "-e", ".[in-airflow]"],
        check=True,
        capture_output=True,
        text=True,
        cwd=path_to_package,
    )
    assert (
        install_result.returncode == 0
    ), f"Failed to install package in virtual environment: {install_result.stderr}"

    uv_pip_freeze_output = subprocess.run(
        [*uv_entrypoint, "pip", "freeze"], check=True, capture_output=True, text=True
    )
    assert (
        install_result.returncode == 0
    ), f"Failed to get pip freeze output: {uv_pip_freeze_output.stderr}"
    assert (
        "dagster-airlift" in uv_pip_freeze_output.stdout
    ), "dagster-airlift not found in pip freeze output"

    # Run the import script
    import_script_path = Path(__file__).parent / "import_script.py"
    script_result = subprocess.run(
        [python_executable, import_script_path], check=True, capture_output=True, text=True
    )
    assert script_result.returncode == 0, f"Script execution failed: {script_result.stderr}"

    # Install Airflow
    airflow_install_result = subprocess.run(
        [*uv_entrypoint, "pip", "install", "apache-airflow"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert (
        airflow_install_result.returncode == 0
    ), f"Failed to install Airflow: {airflow_install_result.stderr}"

    import_airflow_script_path = Path(__file__).parent / "import_script_with_airflow.py"
    airflow_script_result = subprocess.run(
        [python_executable, import_airflow_script_path], check=True, capture_output=True, text=True
    )
    assert (
        airflow_script_result.returncode == 0
    ), f"Script execution failed: {airflow_script_result.stderr}"
