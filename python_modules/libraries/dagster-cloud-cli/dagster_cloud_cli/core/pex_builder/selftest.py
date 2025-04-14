# Simple environment test script

import os
import pprint
import sys

from . import util

if __name__ == "__main__":
    print("hello from selftest.py")
    print(f"sys.executable: {sys.executable}")
    print(f"sys.argv: {sys.argv}")
    pex_environ = {name: value for name, value in os.environ.items() if name.startswith("PEX")}
    print("pex environment:")
    pprint.pprint(pex_environ)

    proc = util.run_pex_command(["--version"])
    print("Pex version:", proc.stdout.decode("utf-8"))

    proc = util.run_dagster_cloud_cli_command(["--version"])
    print(proc.stdout.decode("utf-8"))

    proc = util.run_dagster_command(["--version"])
    print(proc.stdout.decode("utf-8"))

    print("All OK.")
