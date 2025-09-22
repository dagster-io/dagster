from pathlib import Path

from dagster import definitions, load_from_defs_folder

"""
dg dev location config

host: localhost
socket: /var/folders/2t/9xn6r7vx11s1rzxgphjgx0w80000gn/T/tmpcw7g4s3u
module_name: in_app_check_components.definitions
working_directory: /Users/jamie/dev/dagster/python_modules/dagster-test/dagster_test/toys/in_app_check_components/src

cloud location config

location_name: components_in_app_checks
code_source:
  module_name: dagster_test.toys.in_app_check_components.src.in_app_check_components.definitions
  working_directory: /Users/jamie/dev/dagster/python_modules/dagster-test/dagster_test/toys/in_app_check_components/src


  python_file: dagster_test/toys/in_app_check_components/src/in_app_check_components/definitions.py
"""


@definitions
def defs():
    return load_from_defs_folder(path_within_project=Path(__file__).parent)
