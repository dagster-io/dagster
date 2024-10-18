# ruff: noqa: T201
import argparse
import itertools
import subprocess
import sys
from typing import List, Optional

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
parser.add_argument("--include-prebuilt-grpcio-wheel", action="store_true")
parser.add_argument(
    "--system",
    action="store_true",
    help="Install the packages into the system Python. Should only be used in Dockferfiles or CI/CD.",
)


def main(
    quiet: bool,
    extra_packages: List[str],
    include_prebuilt_grpcio_wheel: Optional[bool],
    system: Optional[bool],
) -> None:
    """Especially on macOS, there may be missing wheels for new major Python versions, which means that
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

    # Not all libs are supported on all Python versions. Consult `dagster_buildkite.steps.packages`
    # as the source of truth on which packages support which Python versions. The building of
    # `install_targets` below should use `sys.version_info` checks to reflect this.

    # Supported on all Python versions.
    editable_target_paths = [
        "python_modules/dagster[pyright,ruff,test]",
        "python_modules/dagster-pipes",
        "python_modules/dagster-graphql",
        "python_modules/dagster-test",
        "python_modules/dagster-webserver",
        "python_modules/dagit",
        "python_modules/automation",
        "python_modules/libraries/dagster-managed-elements",
        "python_modules/libraries/dagster-airbyte",
        "python_modules/libraries/dagster-aws[stubs,test]",
        "python_modules/libraries/dagster-celery",
        "python_modules/libraries/dagster-celery-docker",
        "python_modules/libraries/dagster-dask[yarn,pbs,kube]",
        "python_modules/libraries/dagster-databricks",
        "python_modules/libraries/dagster-datadog",
        "python_modules/libraries/dagster-datahub",
        "python_modules/libraries/dagster-dbt",
        "python_modules/libraries/dagster-docker",
        "python_modules/libraries/dagster-gcp",
        "python_modules/libraries/dagster-gcp-pandas",
        "python_modules/libraries/dagster-gcp-pyspark",
        "python_modules/libraries/dagster-embedded-elt",
        "python_modules/libraries/dagster-fivetran",
        "python_modules/libraries/dagster-k8s",
        "python_modules/libraries/dagster-celery-k8s",
        "python_modules/libraries/dagster-github",
        "python_modules/libraries/dagster-mlflow",
        "python_modules/libraries/dagster-mysql",
        "python_modules/libraries/dagster-looker",
        "python_modules/libraries/dagster-openai",
        "python_modules/libraries/dagster-pagerduty",
        "python_modules/libraries/dagster-pandas",
        "python_modules/libraries/dagster-papertrail",
        "python_modules/libraries/dagster-postgres",
        "python_modules/libraries/dagster-prometheus",
        "python_modules/libraries/dagster-pyspark",
        "python_modules/libraries/dagster-shell",
        "python_modules/libraries/dagster-slack",
        "python_modules/libraries/dagster-spark",
        "python_modules/libraries/dagster-ssh",
        "python_modules/libraries/dagster-twilio",
        "python_modules/libraries/dagstermill",
        "integration_tests/python_modules/dagster-k8s-test-infra",
        "python_modules/libraries/dagster-azure",
        "python_modules/libraries/dagster-msteams",
        "python_modules/libraries/dagster-deltalake",
        "python_modules/libraries/dagster-deltalake-pandas",
        "python_modules/libraries/dagster-deltalake-polars",
        "helm/dagster/schema[test]",
        ".buildkite/dagster-buildkite",
        "examples/experimental/dagster-blueprints",
        "examples/experimental/dagster-airlift[core,in-airflow,mwaa,dbt,test]",
    ]

    if sys.version_info <= (3, 12):
        editable_target_paths += [
            "python_modules/libraries/dagster-duckdb",
            "python_modules/libraries/dagster-duckdb-pandas",
            "python_modules/libraries/dagster-duckdb-polars",
            "python_modules/libraries/dagster-duckdb-pyspark",
            "python_modules/libraries/dagster-wandb",
            "python_modules/libraries/dagster-airflow",
        ]

    if sys.version_info > (3, 7):
        editable_target_paths += [
            "python_modules/libraries/dagster-pandera",
            "python_modules/libraries/dagster-snowflake",
            "python_modules/libraries/dagster-snowflake-pandas",
            "python_modules/libraries/dagster-polars[deltalake,gcp,test]",
        ]

    install_targets += list(
        itertools.chain.from_iterable(
            zip(["-e"] * len(editable_target_paths), editable_target_paths)
        )
    )

    if sys.version_info > (3, 6) and sys.version_info < (3, 10):
        install_targets += []

    if include_prebuilt_grpcio_wheel:
        install_targets += [
            "--find-links",
            "https://github.com/dagster-io/build-grpcio/wiki/Wheels",
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

    # Ensure uv is installed which we use for faster package resolution
    subprocess.run(["pip", "install", "-U", "uv"], check=True)

    # NOTE: These need to be installed as one long pip install command, otherwise pip will install
    # conflicting dependencies, which will break pip freeze snapshot creation during the integration
    # image build!
    cmd = ["uv", "pip", "install"] + (["--system"] if system else []) + install_targets

    # Force compat mode for editable installs to avoid
    # polluting uv cache for pyright install
    # See https://github.com/dagster-io/dagster/pull/24212
    # and https://github.com/astral-sh/uv/issues/7028
    cmd += ["--config-settings", "editable-mode=compat"]

    if quiet is not None:
        cmd.append(f'-{"q" * quiet}')

    print(" ".join(cmd))
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    args = parser.parse_args()
    main(
        quiet=args.quiet,
        extra_packages=args.packages,
        include_prebuilt_grpcio_wheel=args.include_prebuilt_grpcio_wheel,
        system=args.system,
    )
