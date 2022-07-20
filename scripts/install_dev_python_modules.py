# pylint: disable=print-call
import argparse
import subprocess
import sys
from typing import List

# We allow extra packages to be passed in via the command line because pip's version resolution
# requires everything to be installed at the same time.

parser = argparse.ArgumentParser()
parser.add_argument("-q", "--quiet", action="count")
parser.add_argument(
    "packages",
    type=str,
    nargs="*",
    help="Additional packages (with optional version reqs) to pass to `pip install`",
)


def main(quiet: bool, extra_packages: List[str]) -> None:
    """
    Especially on macOS, there may be missing wheels for new major Python versions, which means that
    some dependencies may have to be built from source. You may find yourself needing to install
    system packages such as freetype, gfortran, etc.; on macOS, Homebrew should suffice.
    """

    # Previously, we did a pip install --upgrade pip here. We have removed that and instead
    # depend on the user to ensure an up-to-date pip is installed and available. If you run into
    # build errors, try this first. For context, there is a lengthy discussion here:
    # https://github.com/pypa/pip/issues/5599

    install_targets: List[str] = [
        *extra_packages,
    ]

    # Dev tools.
    install_targets += [
        "-r python_envs/requirements-black.txt",
        "-r python_envs/requirements-docker.txt",
        "-r python_envs/requirements-grpc.txt",
        "-r python_envs/requirements-isort.txt",
        "-r python_envs/requirements-mypy.txt",
        "-r python_envs/requirements-pylint.txt",
        "-r python_envs/requirements-tox.txt",
        "-r python_envs/requirements-yamllint.txt",
    ]

    # Not all libs are supported on all Python versions. Consult `dagster_buildkite.steps.packages`
    # as the source of truth on which packages support which Python versions. The building of
    # `install_targets` below should use `sys.version_info` checks to reflect this.

    # Supported on all Python versions.
    install_targets += [
        "-e python_modules/dagster[test]",
        "-e python_modules/dagster-graphql",
        "-e python_modules/dagster-test",
        "-e python_modules/dagit",
        "-e python_modules/automation",
        "-e python_modules/libraries/dagster-airbyte",
        "-e python_modules/libraries/dagster-airflow",
        "-e python_modules/libraries/dagster-aws[test]",
        "-e python_modules/libraries/dagster-celery",
        "-e python_modules/libraries/dagster-celery-docker",
        '-e "python_modules/libraries/dagster-dask[yarn,pbs,kube]"',
        "-e python_modules/libraries/dagster-databricks",
        "-e python_modules/libraries/dagster-datadog",
        "-e python_modules/libraries/dagster-datahub",
        "-e python_modules/libraries/dagster-docker",
        "-e python_modules/libraries/dagster-gcp",
        "-e python_modules/libraries/dagster-fivetran",
        "-e python_modules/libraries/dagster-k8s",
        "-e python_modules/libraries/dagster-celery-k8s",
        "-e python_modules/libraries/dagster-github",
        "-e python_modules/libraries/dagster-mlflow",
        "-e python_modules/libraries/dagster-mysql",
        "-e python_modules/libraries/dagster-pagerduty",
        "-e python_modules/libraries/dagster-pandas",
        "-e python_modules/libraries/dagster-papertrail",
        "-e python_modules/libraries/dagster-postgres",
        "-e python_modules/libraries/dagster-prometheus",
        "-e python_modules/libraries/dagster-pyspark",
        "-e python_modules/libraries/dagster-shell",
        "-e python_modules/libraries/dagster-slack",
        "-e python_modules/libraries/dagster-spark",
        "-e python_modules/libraries/dagster-ssh",
        "-e python_modules/libraries/dagster-twilio",
        "-e python_modules/libraries/dagstermill",
        "-e integration_tests/python_modules/dagster-k8s-test-infra",
        "-e python_modules/libraries/dagster-azure",
        "-e python_modules/libraries/dagster-msteams",
        "-e helm/dagster/schema[test]",
    ]

    if sys.version_info > (3, 7):
        install_targets += [
            "-e python_modules/libraries/dagster-dbt",
            "-e python_modules/libraries/dagster-pandera",
            "-e python_modules/libraries/dagster-snowflake",
            "-e python_modules/libraries/dagster-snowflake-pandas",
        ]

    if sys.version_info > (3, 6) and sys.version_info < (3, 10):
        install_targets += [
            "-e python_modules/libraries/dagster-dbt",
        ]

    # NOTE: `dagster-ge` is out of date and does not support recent versions of great expectations.
    # Because of this, it has second-order dependencies on old versions of popular libraries like
    # numpy which conflict with the requirements of our other libraries. For this reason, until
    # dagster-ge is updated we won't install `dagster-ge` in the common dev environment or
    # pre-install its dependencies in our BK images (which this script is used for).
    #
    # dagster-ge depends on a great_expectations version that does not install on Windows
    # https://github.com/dagster-io/dagster/issues/3319
    # if sys.version_info >= (3, 7) and os.name != "nt":
    #     install_targets += ["-e python_modules/libraries/dagster-ge"]

    # NOTE: These need to be installed as one long pip install command, otherwise pip will install
    # conflicting dependencies, which will break pip freeze snapshot creation during the integration
    # image build!
    cmd = ["pip", "install"] + install_targets

    if quiet is not None:
        cmd.append(f'-{"q" * quiet}')

    p = subprocess.Popen(
        " ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )
    print(" ".join(cmd))
    while True:
        output = p.stdout.readline()  # type: ignore
        if p.poll() is not None:
            break
        if output:
            print(output.decode("utf-8").strip())


if __name__ == "__main__":
    args = parser.parse_args()
    main(quiet=args.quiet, extra_packages=args.packages)
