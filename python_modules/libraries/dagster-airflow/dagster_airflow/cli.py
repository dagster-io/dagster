import os
from datetime import datetime, timedelta

import click

import dagster._check as check
from dagster._cli.load_handle import recon_repo_for_cli_args
from dagster._utils import load_yaml_from_glob_list
from dagster._utils.backcompat import canonicalize_backcompat_args
from dagster._utils.indenting_printer import IndentingStringIoPrinter
from dagster._utils.yaml_utils import dump_run_config_yaml


def construct_environment_yaml(preset_name, config, pipeline_name, module_name):
    # Load environment dict from either a preset or yaml file globs
    cli_args = {
        "fn_name": pipeline_name,
        "module_name": module_name,
    }

    pipeline_def = recon_repo_for_cli_args(cli_args).get_definition().get_pipeline(pipeline_name)

    if preset_name:
        if config:
            raise click.UsageError("Can not use --preset with --config.")

        run_config = pipeline_def.get_preset(preset_name).run_config

    else:
        config = list(config)
        run_config = load_yaml_from_glob_list(config) if config else {}

    return run_config


def construct_scaffolded_file_contents(module_name, job_name, run_config):
    yesterday = datetime.now() - timedelta(1)

    printer = IndentingStringIoPrinter(indent_level=4)
    printer.line("'''")
    printer.line(
        "The airflow DAG scaffold for {module_name}.{job_name}".format(
            module_name=module_name, job_name=job_name
        )
    )
    printer.blank_line()
    printer.line('Note that this docstring must contain the strings "airflow" and "DAG" for')
    printer.line("Airflow to properly detect it as a DAG")
    printer.line("See: http://bit.ly/307VMum")
    printer.line("'''")
    printer.line("import datetime")
    printer.blank_line()
    printer.line("import yaml")
    printer.line("from dagster_airflow.factory import make_airflow_dag")
    printer.blank_line()
    printer.line("#" * 80)
    printer.comment("#")
    printer.comment("# This environment is auto-generated from your configs and/or presets")
    printer.comment("#")
    printer.line("#" * 80)
    printer.line("ENVIRONMENT = '''")
    printer.line(dump_run_config_yaml(run_config))
    printer.line("'''")
    printer.blank_line()
    printer.blank_line()
    printer.line("#" * 80)
    printer.comment("#")
    printer.comment("# NOTE: these arguments should be edited for your environment")
    printer.comment("#")
    printer.line("#" * 80)
    printer.line("DEFAULT_ARGS = {")
    with printer.with_indent():
        printer.line("'owner': 'airflow',")
        printer.line("'depends_on_past': False,")

        # start date -> yesterday
        printer.line(
            "'start_date': datetime.datetime(%s, %d, %d),"
            % (yesterday.year, yesterday.month, yesterday.day)
        )
        printer.line("'email': ['airflow@example.com'],")
        printer.line("'email_on_failure': False,")
        printer.line("'email_on_retry': False,")
    printer.line("}")
    printer.blank_line()
    printer.line("dag, tasks = make_airflow_dag(")
    with printer.with_indent():
        printer.comment(f"NOTE: you must ensure that {module_name} is ")
        printer.comment("installed or available on sys.path, otherwise, this import will fail.")
        printer.line(f"module_name='{module_name}',")
        printer.line(f"job_name='{job_name}',")
        printer.line("run_config=yaml.safe_load(ENVIRONMENT),")
        printer.line("dag_kwargs={'default_args': DEFAULT_ARGS, 'max_active_runs': 1}")
    printer.line(")")

    return printer.read().encode("utf-8")


@click.group()
def main():
    pass


@main.command()
@click.option(
    "--module-name", "-m", type=click.STRING, help="The name of the source module", required=True
)
@click.option("--pipeline-name", type=click.STRING, help="The name of the pipeline")
@click.option(
    "--output-path",
    "-o",
    type=click.Path(),
    help="Optional. If unset, $AIRFLOW_HOME will be used.",
    default=os.getenv("AIRFLOW_HOME"),
)
@click.option(
    "-c",
    "--config",
    type=click.STRING,
    multiple=True,
    help=(
        "Specify one or more run config files. These can also be file patterns. "
        "If more than one run config file is captured then those files are merged. "
        "Files listed first take precendence. They will smash the values of subsequent "
        "files at the key-level granularity. If the file is a pattern then you must "
        "enclose it in double quotes"
    ),
)
@click.option(
    "-p",
    "--preset",
    type=click.STRING,
    help="Specify a preset to use for this pipeline. Presets are defined on pipelines under "
    "preset_defs.",
)
@click.option("--job-name", type=click.STRING, help="The name of the job")
def scaffold(module_name, pipeline_name, output_path, config, preset, job_name):
    """Creates a DAG file for a specified dagster pipeline"""
    job_name = canonicalize_backcompat_args(
        new_val=job_name,
        new_arg="job_name",
        old_val=pipeline_name,
        old_arg="pipeline_name",
        breaking_version="future versions",
        coerce_old_to_new=lambda val: val,
    )

    check.invariant(job_name is not None, "You must specify either --job-name or --pipeline-name.")
    check.tuple_param(config, "config", of_type=str)
    check.invariant(isinstance(config, tuple))
    check.invariant(
        output_path is not None,
        "You must specify --output-path or set AIRFLOW_HOME to use this script.",
    )

    run_config = construct_environment_yaml(preset, config, job_name, module_name)
    file_contents = construct_scaffolded_file_contents(module_name, job_name, run_config)

    # Ensure output_path/dags exists
    dags_path = os.path.join(os.path.expanduser(output_path), "dags")
    if not os.path.isdir(dags_path):
        os.makedirs(dags_path)

    dag_file = os.path.join(os.path.expanduser(output_path), "dags", job_name + ".py")

    click.echo("Wrote DAG scaffold to file: %s" % dag_file)

    with open(dag_file, "wb") as f:
        f.write(file_contents)


if __name__ == "__main__":
    main()  # pylint:disable=no-value-for-parameter
