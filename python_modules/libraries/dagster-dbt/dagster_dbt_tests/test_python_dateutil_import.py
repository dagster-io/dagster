import subprocess
import sys


def test_modules_import_without_python_dateutil() -> None:
    # python-dateutil is not a declared dependency of dagster-dbt, so none of its modules
    # may import it directly. Setting the entry to None makes `import dateutil` raise.
    code = "\n".join(
        [
            "import sys",
            "sys.modules['dateutil'] = None",
            "import dagster_dbt",
            "import dagster_dbt.cloud.utils",
            "import dagster_dbt.cloud_v2.run_handler",
            "import dagster_dbt.core.dbt_cli_event",
        ]
    )
    subprocess.run([sys.executable, "-c", code], check=True)
