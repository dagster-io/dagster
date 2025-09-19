from pathlib import Path

from dagster import definitions, load_from_defs_folder

"""
add to local cloud dev with

location_name: components_in_app_checks
code_source:
  module_name: dagster_test.toys.components_in_app_checks.src.components_in_app_checks.definitions
"""


@definitions
def defs():
    print(f"HERE THE PATH IS: {Path(__file__).parent}")
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
