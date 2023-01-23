"""
This script installs dagster and its dependencies into the current Python environment.

Run as `python3 install_dagster.py`.
To install in a venv, run python from the venv: `/path/to/venv/bin/python3 install_dagster.py`
"""

import platform
import subprocess
import sys

# pylint: disable=missing-function-docstring
# pylint: disable=consider-using-f-string


class InstallFailed(Exception):
    """Unexpected installation failure"""


def pip(*args):
    return subprocess.run(
        [sys.executable, "-m", "pip", *args], capture_output=True, check=False, encoding="utf-8"
    )


def has_pip():
    proc = pip("-V")
    return proc.returncode == 0


def installed_packages():
    proc = pip("freeze")
    if proc.returncode:
        raise InstallFailed("Could not determine installed packages", sys.stderr)
    return dict(line.split("==", 1) for line in proc.stdout.splitlines(keepends=False) if "==" in line)


def check_python():
    version_str = "{}.{}.{}".format(*sys.version_info[:3])
    python_str = "{} (version {})".format(sys.executable, version_str)
    errors = []
    if sys.version_info < (3, 7):
        errors.append("dagster requires Python 3.7 or newer, found version {}".format(version_str))
    return ("Python executable", python_str, errors)


def check_python_env():
    errors = []
    if not has_pip():
        errors.append("pip is required to install dagster and was not found")
    else:
        packages = installed_packages()
        if "dagster" in packages:
            errors.append("dagster version {} is already installed".format(packages["dagster"]))
            errors.append("To upgrade, run 'pip install dagster --upgrade'")

    return ("Python environment", sys.prefix, errors)


def check_platform():
    return ("Platform", platform.platform(), [])


def main():
    print()
    print("✨✨✨ Welcome to dagster! ✨✨✨")
    print()
    print("This will install the latest version of dagster and its dependencies.")
    print()
    print("Inspecting this system:")

    failed = False
    for check in [check_python, check_python_env, check_platform]:
        label, value, errors = check()
        if errors:
            print(" ❌ {}: {}".format(label, value))
            for error in errors:
                print("    ➤ {}".format(error))
                failed = True 
        else:
            print(" ✅ {}: {}".format(label, value))
    print()
    if failed:
        print("Cannot install dagster due to above errors.")
        return 1

    print("Installing dagster and dagit:")
    proc = pip("install", "dagster", "dagit", "--find-links=https://github.com/dagster-io/build-grpcio/wiki/Wheels")
    if proc.returncode:
        print("❌ failed to install dagster:")
        print(proc.stderr)
    else:
        print(" ✅ successfully installed dagster and its dependencies")
        print("    ➤ you can now run 'dagster -h' or visit https://dagster.io to learn more")

if __name__ == "__main__":
    sys.exit(main())
