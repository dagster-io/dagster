# ruff: isort: skip_file

import time

time.sleep(20)

from dagster_tests.general_tests.grpc_tests.grpc_repo import bar_repo  # noqa: F401
