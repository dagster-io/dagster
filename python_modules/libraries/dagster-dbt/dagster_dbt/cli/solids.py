from dagster import (
    Array,
    Bool,
    InputDefinition,
    Noneable,
    Nothing,
    Output,
    OutputDefinition,
    Permissive,
    StringSource,
    solid,
)
from dagster.config.field import Field
from dagster.utils.backcompat import experimental

from ..utils import generate_materializations
from .constants import (
    CLI_COMMON_FLAGS_CONFIG_SCHEMA,
    CLI_COMMON_OPTIONS_CONFIG_SCHEMA,
    DEFAULT_DBT_TARGET_PATH,
)
from .types import DbtCliOutput
from .utils import execute_cli

CLI_CONFIG_SCHEMA = {**CLI_COMMON_FLAGS_CONFIG_SCHEMA, **CLI_COMMON_OPTIONS_CONFIG_SCHEMA}
CLI_COMMON_FLAGS = set(CLI_COMMON_FLAGS_CONFIG_SCHEMA.keys())


def passthrough_flags_only(solid_config, additional_flags):
    return {
        flag: solid_config[flag]
        for flag in (CLI_COMMON_FLAGS | set(additional_flags))
        if solid_config.get(flag) is not None
    }


@solid(
    description="A solid to invoke dbt run via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides settings "
                "in profiles.yml."
            ),
        ),
        "models": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to run.",
        ),
        "exclude": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "full-refresh": Field(
            config=bool,
            description=(
                "If specified, DBT will drop incremental models and fully-recalculate the "
                "incremental table from the model definition. (--full-refresh)"
            ),
            is_required=False,
            default_value=False,
        ),
        "fail-fast": Field(
            config=bool,
            description="Stop execution upon a first failure. (--fail-fast)",
            is_required=False,
            default_value=False,
        ),
        "yield_materializations": Field(
            config=Bool,
            is_required=False,
            default_value=True,
            description=(
                "If True, materializations corresponding to the results of the dbt operation will "
                "be yielded when the solid executes. Default: True"
            ),
        ),
        "asset_key_prefix": Field(
            config=Array(str),
            is_required=False,
            default_value=[],
            description=(
                "If provided and yield_materializations is True, these components will be used to "
                "prefix the generated asset keys."
            ),
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_run(context):
    """This solid executes ``dbt run`` via the dbt CLI. See the solid definition for available
    parameters.
    """

    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="run",
        flags_dict=passthrough_flags_only(
            context.solid_config, ("threads", "models", "exclude", "full-refresh", "fail-fast")
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    if context.solid_config["yield_materializations"]:
        for materialization in generate_materializations(
            cli_output,
            asset_key_prefix=context.solid_config["asset_key_prefix"],
        ):
            yield materialization

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt test via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "data": Field(
            config=bool,
            description='Run data tests defined in "tests" directory.',
            is_required=False,
            default_value=False,
        ),
        "schema": Field(
            config=bool,
            description="Run constraint validations from schema.yml files.",
            is_required=False,
            default_value=False,
        ),
        "fail-fast": Field(
            config=bool,
            description="Stop execution upon a first test failure.",
            is_required=False,
            default_value=False,
        ),
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides settings "
                "in profiles.yml."
            ),
        ),
        "models": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to run.",
        ),
        "exclude": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "target-path": Field(
            config=StringSource,
            is_required=False,
            default_value=DEFAULT_DBT_TARGET_PATH,
            description=(
                "The directory path for target if different from the default `target-path` in "
                "your dbt project configuration file."
            ),
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_test(context):
    """This solid executes ``dbt test`` via the dbt CLI. See the solid definition for available
    parameters.
    """
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="test",
        flags_dict=passthrough_flags_only(
            context.solid_config, ("data", "schema", "fail-fast", "threads", "models", "exclude")
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt snapshot via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides settings in "
                "profiles.yml."
            ),
        ),
        "select": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to include.",
        ),
        "exclude": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_snapshot(context):
    """This solid executes ``dbt snapshot`` via the dbt CLI."""
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="snapshot",
        flags_dict=passthrough_flags_only(context.solid_config, ("threads", "select", "exclude")),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt run-operation via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "macro": Field(
            config=StringSource,
            description=(
                "Specify the macro to invoke. dbt will call this macro with the supplied "
                "arguments and then exit."
            ),
        ),
        "args": Field(
            config=Permissive({}),
            is_required=False,
            description=(
                "Supply arguments to the macro. This dictionary will be mapped to the keyword "
                "arguments defined in the selected macro. This argument should be a dictionary, "
                "eg. {'my_variable': 'my_value'}"
            ),
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_run_operation(context):
    """This solid executes ``dbt run-operation`` via the dbt CLI."""
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command=f"run-operation {context.solid_config['macro']}",
        flags_dict=passthrough_flags_only(context.solid_config, ("args",)),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt source snapshot-freshness via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "select": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="Specify the sources to snapshot freshness.",
        ),
        "output": Field(
            config=StringSource,
            is_required=False,
            description=(
                "Specify the output path for the json report. By default, outputs to "
                "target/sources.json"
            ),
        ),
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides "
                "settings in profiles.yml."
            ),
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_snapshot_freshness(context):
    """This solid executes ``dbt source snapshot-freshness`` via the dbt CLI."""
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="source snapshot-freshness",
        flags_dict=passthrough_flags_only(context.solid_config, ("select", "output", "threads")),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt compile via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "parse-only": Field(
            config=bool,
            is_required=False,
            default_value=False,
        ),
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides settings "
                "in profiles.yml."
            ),
        ),
        "no-version-check": Field(
            config=bool,
            description=(
                "Skip the check that dbt's version matches the one specified in the "
                "dbt_project.yml file ('require-dbt-version')"
            ),
            is_required=False,
            default_value=False,
        ),
        "models": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to run.",
        ),
        "exclude": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "selector": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The selector name to use, as defined in your selectors.yml",
        ),
        "state": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description=(
                "If set, use the given directory as the source for json files to compare with "
                "this project."
            ),
        ),
        "full-refresh": Field(
            config=bool,
            description=(
                "If specified, DBT will drop incremental models and fully-recalculate "
                "the incremental table from the model definition. (--full-refresh)"
            ),
            is_required=False,
            default_value=False,
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_compile(context):
    """This solid executes ``dbt compile`` via the dbt CLI."""
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="compile",
        flags_dict=passthrough_flags_only(
            context.solid_config,
            (
                "parse-only",
                "threads",
                "no-version-check",
                "models",
                "exclude",
                "selector",
                "state",
                "full-refresh",
            ),
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt docs generate via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides settings "
                "in profiles.yml."
            ),
        ),
        "no-version-check": Field(
            config=bool,
            description=(
                "Skip the check that dbt's version matches the one specified in the "
                "dbt_project.yml file ('require-dbt-version')"
            ),
            is_required=False,
            default_value=False,
        ),
        "models": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to run.",
        ),
        "exclude": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "selector": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The selector name to use, as defined in your selectors.yml",
        ),
        "state": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description=(
                "If set, use the given directory as the source for json files to compare with "
                "this project."
            ),
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_docs_generate(context):
    """This solid executes ``dbt docs generate`` via the dbt CLI."""
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="docs generate",
        flags_dict=passthrough_flags_only(
            context.solid_config,
            (
                "threads",
                "no-version-check",
                "models",
                "exclude",
                "selector",
                "state",
            ),
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")


@solid(
    description="A solid to invoke dbt seed via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="dbt_cli_output", dagster_type=DbtCliOutput)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "full-refresh": Field(
            config=bool,
            default_value=False,
            is_required=False,
            description=("Drop existing seed tables and recreate them."),
        ),
        "show": Field(
            config=bool,
            default_value=False,
            is_required=False,
            description=("Show a sample of the loaded data in the terminal."),
        ),
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description=(
                "Specify number of threads to use while executing models. Overrides settings "
                "in profiles.yml."
            ),
        ),
        "no-version-check": Field(
            config=bool,
            description=(
                "Skip the check that dbt's version matches the one specified in the "
                "dbt_project.yml file ('require-dbt-version')"
            ),
            is_required=False,
            default_value=False,
        ),
        "select": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="Specify the nodes to include.",
        ),
        "exclude": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The dbt models to exclude.",
        ),
        "selector": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description="The selector name to use, as defined in your selectors.yml",
        ),
        "state": Field(
            config=Noneable([str]),
            default_value=None,
            is_required=False,
            description=(
                "If set, use the given directory as the source for json files to compare with "
                "this project."
            ),
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_seed(context):
    """This solid executes ``dbt seed`` via the dbt CLI."""
    cli_output = execute_cli(
        context.solid_config["dbt_executable"],
        command="seed",
        flags_dict=passthrough_flags_only(
            context.solid_config,
            (
                "full-refresh",
                "show",
                "threads",
                "no-version-check",
                "select",
                "exclude",
                "selector",
                "state",
            ),
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
        target_path=context.solid_config["target-path"],
    )

    yield Output(cli_output, "dbt_cli_output")
