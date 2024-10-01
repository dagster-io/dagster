import argparse

from perf_harness.shared.constants import get_num_dags, get_num_tasks
from perf_harness.shared.utils import scaffold_migration_state

# Set up argument parser
parser = argparse.ArgumentParser(
    description="Generate YAML files with a specified migration state."
)
parser.add_argument(
    "migration_state", type=str, help="The migration state to use in the YAML files"
)

# Parse arguments
args = parser.parse_args()

scaffold_migration_state(get_num_dags(), get_num_tasks(), args.migration_state == "True")
