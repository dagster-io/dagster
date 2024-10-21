import argparse

from perf_harness.shared.constants import get_num_dags, get_num_tasks
from perf_harness.shared.utils import scaffold_proxied_state

# Set up argument parser
parser = argparse.ArgumentParser(description="Generate YAML files with a specified proxied state.")
parser.add_argument("proxied_state", type=str, help="The proxied state to use in the YAML files")

# Parse arguments
args = parser.parse_args()

scaffold_proxied_state(get_num_dags(), get_num_tasks(), args.proxied_state == "True")
