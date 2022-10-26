# pylint: disable=print-call
import os
import subprocess
import tempfile
from pathlib import Path

from dagster._cli.debug import export_run

from .integration_utils import IS_BUILDKITE


def current_test():
    # example PYTEST_CURRENT_TEST: test_user_code_deployments.py::test_execute_on_celery_k8s (teardown)
    return (
        os.environ.get("PYTEST_CURRENT_TEST")
        .split()[0]
        .replace("::", "-")
        .replace(".", "-")
        .replace("/", "-")
    )


def upload_buildkite_artifact(artifact_file):
    if IS_BUILDKITE:
        print(f"Uploading artifact to Buildkite: {artifact_file}")
        p = subprocess.Popen(
            [
                "buildkite-agent",
                "artifact",
                "upload",
                artifact_file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = p.communicate()
        print("Buildkite artifact added with stdout: ", stdout)
        print("Buildkite artifact added with stderr: ", stderr)
        assert p.returncode == 0


def export_runs(instance):
    for run in instance.get_runs():
        with tempfile.TemporaryDirectory() as tempdir:
            output_file = Path(tempdir) / f"{current_test()}-{run.run_id}.txt"
            output_file.touch()

        try:
            export_run(instance, run, output_file)
        except Exception as e:
            print(f"Hit an error exporting dagster-debug {output_file}: {e}")
            continue
        upload_buildkite_artifact(output_file)


def export_postgres(url):
    with tempfile.TemporaryDirectory() as tempdir:
        output_file = Path(tempdir) / f"{current_test()}-postgres.txt"
        output_file.touch()
        subprocess.run(["pg_dump", url, "-f", output_file], check=False)
        upload_buildkite_artifact(output_file)


def export_kind():
    with tempfile.TemporaryDirectory() as tempdir:
        output_directory = Path(tempdir) / "kind-info-dump"
        subprocess.run(
            [
                "kubectl",
                "cluster-info",
                "dump",
                "--all-namespaces=true",
                "--output-directory={output_directory}".format(
                    output_directory=str(output_directory)
                ),
            ],
            check=False,
        )

    upload_buildkite_artifact(str(output_directory / "**" / "*"))
