# This file is temporary to decouple D5777 from changing the Buildkite web UI. Will be removed
# in a follow-up diff
import subprocess


def main():
    res = subprocess.check_call(
        "python3 -m pip install --user -e .buildkite/dagster-buildkite &> /dev/null", shell=True
    )
    assert res == 0

    buildkite_yaml = subprocess.check_output("~/.local/bin/dagster-buildkite", shell=True)
    print(buildkite_yaml)  # pylint: disable=print-call


if __name__ == "__main__":
    main()
