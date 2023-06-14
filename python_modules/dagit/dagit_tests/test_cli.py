import subprocess


def test_invoke_cli():
    process = subprocess.Popen(
        ["dagit", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, _ = process.communicate()
    assert process.returncode == 0
    assert b"dagster-webserver, version" in stdout
