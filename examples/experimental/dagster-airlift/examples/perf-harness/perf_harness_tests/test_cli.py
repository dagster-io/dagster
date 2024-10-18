import subprocess
from pathlib import Path

expected_lines = [
    "Total airflow dags load time",
    "Airflow defs import time",
    "Proxying to dagster time",
    "Airflow setup time",
    "Airflow standup time",
    "Peered defs import time",
    "Observed defs import time",
    "Migrate defs import time",
    "peer defs initial load time",
    "observe defs initial load time",
    "migrate defs initial load time",
    "peer sensor tick with no runs time",
    "observe sensor tick with no runs time",
    "migrate sensor tick with no runs time",
    "peer sensor tick with single run time",
    "observe sensor tick with single run time",
    "migrate sensor tick with single run time",
    "peer sensor tick with 1 runs time",
    "observe sensor tick with 1 runs time",
    "migrate sensor tick with 1 runs time",
]

makefile_dir = Path(__file__).parent.parent
expected_file = makefile_dir / "perf_harness" / "shared" / "1_dags_1_tasks_perf_output.txt"


def test_cli() -> None:
    """Test that the CLI can be run, and produces expected output."""
    subprocess.call(
        ["make", "run_perf_scenarios_test"], cwd=makefile_dir, stdout=subprocess.DEVNULL
    )
    assert expected_file.exists()
    for i, line in enumerate(expected_file.read_text().split("\n")[:-1]):  # last line is empty
        assert expected_lines[i] in line
