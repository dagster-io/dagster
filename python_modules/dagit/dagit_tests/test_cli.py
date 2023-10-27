import os
import subprocess
import time

from dagster import asset


def test_invoke_cli():
    process = subprocess.Popen(
        ["dagit", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, _ = process.communicate()
    assert process.returncode == 0
    assert b"dagster-webserver, version" in stdout


# This makes this module loadable by dagit
@asset
def foo(bar):
    return 1


def test_cli_logs_to_dagit():
    defs_path = os.path.realpath(__file__)
    process = subprocess.Popen(
        ["dagit", "-f", defs_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    time.sleep(2)  # give time for dagit to start
    process.terminate()
    process.wait()
    stdout, _ = process.communicate()
    assert "The `dagit` CLI command is deprecated" in stdout
    assert "- dagit -" in stdout
