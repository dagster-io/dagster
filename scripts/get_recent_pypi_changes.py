# ruff: noqa: T201

import datetime
import subprocess
import time
from urllib.parse import urlunparse

import requests

# Checks all packages in the current venv, sorts their most recent releases by time, and prints
# anything that has changed in the last N days. Use to detect upstream breakages.

libraries = subprocess.check_output("pip list | cut -f1 -d ' '", shell=True).decode("utf-8")

libraries = libraries.split("\n")

libraries = libraries[2:]

release_times = {}
versions = {}

LAST_N_DAYS = 7

for library in libraries:
    if "dagster" in library:
        continue

    print("Checking " + library + "...")

    if library:
        res_json = requests.get(
            urlunparse(
                (
                    "https",
                    "pypi.org",
                    "/".join(["pypi", library, "json"]),
                    None,
                    None,
                    None,
                )
            )
        ).json()

        if "info" in res_json:
            version = res_json["info"]["version"]
            versions[library] = version
            last_release_info = res_json["releases"][version]

            if len(last_release_info) > 0:
                upload_time = last_release_info[0]["upload_time"]
                release_times[library] = upload_time

print(f"\n\nPyPi releases in the last {LAST_N_DAYS} days:")

now = time.time()

for library, release_time in sorted(release_times.items(), key=lambda item: item[1], reverse=True):
    timestamp = datetime.datetime.strptime(release_time, "%Y-%m-%dT%H:%M:%S").timestamp()
    if now - timestamp > 3600 * 24 * LAST_N_DAYS:
        break

    print(library + " released version " + versions[library] + " at " + release_times[library])
