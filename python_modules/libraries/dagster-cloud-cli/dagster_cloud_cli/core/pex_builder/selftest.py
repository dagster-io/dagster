# Simple environment test script

import os

from dagster_cloud_cli.core.pex_builder import util

if __name__ == "__main__":
    pex_environ = {name: value for name, value in os.environ.items() if name.startswith("PEX")}

    proc = util.run_pex_command(["--version"])

    proc = util.run_dagster_cloud_cli_command(["--version"])

    proc = util.run_dagster_command(["--version"])
