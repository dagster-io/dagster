# pylint: disable=print-call
import os
import subprocess
import sys


def main(quiet):
    """
    Especially on macOS, there may be missing wheels for new major Python versions, which means that
    some dependencies may have to be built from source. You may find yourself needing to install
    system packages such as freetype, gfortran, etc.; on macOS, Homebrew should suffice.
    """

    # Previously, we did a pip install --upgrade pip here. We have removed that and instead
    # depend on the user to ensure an up-to-date pip is installed and available. If you run into
    # build errors, try this first. For context, there is a lengthy discussion here:
    # https://github.com/pypa/pip/issues/5599

    install_targets = [
        "-e python_modules/dagster[black,isort,mypy,test]",
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
        "-e python_modules/libraries/dagster-dbt",
        "-e python_modules/libraries/dagster-docker",
        "-e python_modules/libraries/dagster-gcp",
        "-e python_modules/libraries/dagster-fivetran",
        "-e python_modules/libraries/dagster-k8s",
        "-e python_modules/libraries/dagster-celery-k8s",
        "-e python_modules/libraries/dagster-github",
        "-e python_modules/libraries/dagster-mysql",
        "-e python_modules/libraries/dagster-pagerduty",
        "-e python_modules/libraries/dagster-pandas",
        "-e python_modules/libraries/dagster-pandera",
        "-e python_modules/libraries/dagster-papertrail",
        "-e python_modules/libraries/dagster-postgres",
        "-e python_modules/libraries/dagster-prometheus",
        "-e python_modules/libraries/dagster-pyspark",
        "-e python_modules/libraries/dagster-shell",
        "-e python_modules/libraries/dagster-slack",
        "-e python_modules/libraries/dagster-snowflake",
        "-e python_modules/libraries/dagster-spark",
        "-e python_modules/libraries/dagster-ssh",
        "-e python_modules/libraries/dagster-twilio",
        "-e python_modules/libraries/dagstermill",
        "-e integration_tests/python_modules/dagster-k8s-test-infra",
        "-r scala_modules/scripts/requirements.txt",
        "-e python_modules/libraries/dagster-azure",
        "-e python_modules/libraries/dagster-msteams",
        "-e helm/dagster/schema[test]",
        '-e "examples/airline_demo[full]"',
    ]

    # dagster-ge depends on a great_expectations version that does not install on Windows
    # https://github.com/dagster-io/dagster/issues/3319
    if not os.name == "nt":
        install_targets += ["-e python_modules/libraries/dagster-ge"]

    # NOTE: These need to be installed as one long pip install command, otherwise pip will install
    # conflicting dependencies, which will break pip freeze snapshot creation during the integration
    # image build!
    cmd = ["pip", "install"] + install_targets

    if quiet:
        cmd.append(quiet)

    p = subprocess.Popen(
        " ".join(cmd), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True
    )
    print(" ".join(cmd))
    while True:
        output = p.stdout.readline()   # type: ignore
        if p.poll() is not None:
            break
        if output:
            print(output.decode("utf-8").strip())


if __name__ == "__main__":
    main(quiet=sys.argv[1] if len(sys.argv) > 1 else "")
