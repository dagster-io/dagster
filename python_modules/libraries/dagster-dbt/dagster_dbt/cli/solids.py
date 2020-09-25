from dagster import (
    AssetMaterialization,
    EventMetadataEntry,
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

from .types import DbtCliResult, DbtCliStatsResult
from .utils import execute_dbt, get_run_results

DEFAULT_DBT_EXECUTABLE = "dbt"

# the following config items correspond to flags that apply to all CLI commands
# https://github.com/fishtown-analytics/dbt/blob/dev/marian-anderson/core/dbt/main.py#L260-L329
CLI_COMMON_FLAGS_CONFIG_SCHEMA = {
    "project-dir": Field(
        config=StringSource,
        is_required=False,
        description="Which directory to look in for the dbt_project.yml file. Default is the current working directory and its parents.",
    ),
    "profiles-dir": Field(
        config=StringSource,
        is_required=False,
        description="Which directory to look in for the profiles.yml file. Default = $DBT_PROFILES_DIR or $HOME/.dbt",
    ),
    "profile": Field(
        config=StringSource,
        is_required=False,
        description="Which profile to load. Overrides setting in dbt_project.yml.",
    ),
    "target": Field(
        config=StringSource,
        is_required=False,
        description="Which target to load for the given profile.",
    ),
    "vars": Field(
        config=Permissive({}),
        is_required=False,
        description="Supply variables to the project. This argument overrides variables defined in your dbt_project.yml file. This argument should be a dictionary, eg. {'my_variable': 'my_value'}",
    ),
    "bypass-cache": Field(
        config=bool,
        is_required=False,
        description="If set, bypass the adapter-level cache of database state",
        default_value=False,
    ),
}

# the following are all the config items common to all CLI solids/commands, comprised of the
# base flags applicable to each command and other values that shouldn't be auto-converted to flags
CLI_CONFIG_SCHEMA = {
    **CLI_COMMON_FLAGS_CONFIG_SCHEMA,
    "warn-error": Field(
        config=bool,
        is_required=False,
        description="If dbt would normally warn, instead raise an exception. Examples include --models that selects nothing, deprecations, configurations with no associated models, invalid test configurations, and missing sources/refs in tests.",
        default_value=False,
    ),
    "dbt_executable": Field(
        config=StringSource,
        is_required=False,
        description="Path to the dbt executable. Default is {}".format(DEFAULT_DBT_EXECUTABLE),
        default_value=DEFAULT_DBT_EXECUTABLE,
    ),
    "ignore_handled_error": Field(
        config=bool,
        is_required=False,
        description="When True, will not raise an exception when the dbt CLI returns error code 1. Default is False.",
        default_value=False,
    ),
}

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
    output_defs=[OutputDefinition(name="result", dagster_type=DbtCliStatsResult)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description="Specify number of threads to use while executing models. Overrides settings in profiles.yml.",
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
            description="If specified, DBT will drop incremental models and fully-recalculate the incremental table from the model definition. (--full-refresh)",
            is_required=False,
            default_value=False,
        ),
        "fail-fast": Field(
            config=bool,
            description="Stop execution upon a first failure. (--fail-fast)",
            is_required=False,
            default_value=False,
        ),
    },
    tags={"kind": "dbt"},
)
@experimental
def dbt_cli_run(context) -> DbtCliStatsResult:
    """This solid executes ``dbt run`` via the dbt CLI."""
    logs, raw_output, return_code = execute_dbt(
        context.solid_config["dbt_executable"],
        command=("run",),
        flags_dict=passthrough_flags_only(
            context.solid_config, ("threads", "models", "exclude", "full-refresh", "fail-fast")
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
    )

    run_results = get_run_results(logs)

    yield AssetMaterialization(
        asset_key="dbt_cli_run-shell_output",  # TODO: Perhaps derive asset key from CLI flags?
        description="The output of a shell execution of `dbt run`.",
        metadata_entries=[
            EventMetadataEntry.float(
                label="return_code",
                value=float(return_code),
                description="The return code of a shell exeuction of `dbt run`.",
            ),
            EventMetadataEntry.json(
                label="run_results",
                data=run_results,
                description="The summarized results of a shell execution of `dbt run`.",
            ),
            EventMetadataEntry.text(
                label="raw_output",
                text=raw_output,
                description="The raw output of a shell execution of `dbt run`.",
            ),
        ],
    )

    yield Output(
        DbtCliStatsResult(logs=logs, raw_output=raw_output, return_code=return_code, **run_results)
    )


@solid(
    description="A solid to invoke dbt test via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtCliStatsResult)],
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
            description="Specify number of threads to use while executing models. Overrides settings in profiles.yml.",
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
    },
)
@experimental
def dbt_cli_test(context) -> DbtCliStatsResult:
    """This solid executes ``dbt test`` via the dbt CLI."""
    logs, raw_output, return_code = execute_dbt(
        context.solid_config["dbt_executable"],
        command=("test",),
        flags_dict=passthrough_flags_only(
            context.solid_config, ("data", "schema", "fail-fast", "threads", "models", "exclude")
        ),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
    )

    run_results = get_run_results(logs)

    yield AssetMaterialization(
        asset_key="dbt_cli_test-shell_output",  # TODO: Perhaps derive asset key from CLI flags?
        description="The output of a shell execution of `dbt test`.",
        metadata_entries=[
            EventMetadataEntry.float(
                label="return_code",
                value=float(return_code),
                description="The return code of a shell exeuction of `dbt test`.",
            ),
            EventMetadataEntry.json(
                label="run_results",
                data=run_results,
                description="The summarized results of a shell execution of `dbt test`.",
            ),
            EventMetadataEntry.text(
                label="raw_output",
                text=raw_output,
                description="The raw output of a shell execution of `dbt test`.",
            ),
        ],
    )

    yield Output(
        DbtCliStatsResult(logs=logs, raw_output=raw_output, return_code=return_code, **run_results)
    )


@solid(
    description="A solid to invoke dbt snapshot via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtCliResult)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description="Specify number of threads to use while executing models. Overrides settings in profiles.yml.",
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
    },
)
@experimental
def dbt_cli_snapshot(context) -> DbtCliResult:
    """This solid executes ``dbt snapshot`` via the dbt CLI."""
    logs, raw_output, return_code = execute_dbt(
        context.solid_config["dbt_executable"],
        command=("snapshot",),
        flags_dict=passthrough_flags_only(context.solid_config, ("threads", "models", "exclude")),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
    )

    yield AssetMaterialization(
        asset_key="dbt_cli_snapshot-shell_output",  # TODO: Perhaps derive asset key from CLI flags?
        description="The output of a shell execution of `dbt snapshot`.",
        metadata_entries=[
            EventMetadataEntry.float(
                label="return_code",
                value=float(return_code),
                description="The return code of a shell exeuction of `dbt snapshot`.",
            ),
            EventMetadataEntry.text(
                label="raw_output",
                text=raw_output,
                description="The raw output of a shell execution of `dbt snapshot`.",
            ),
        ],
    )

    yield Output(DbtCliResult(logs=logs, raw_output=raw_output, return_code=return_code))


@solid(
    description="A solid to invoke dbt run-operation via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtCliResult)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "macro": Field(
            config=StringSource,
            description="Specify the macro to invoke. dbt will call this macro with the supplied arguments and then exit.",
        ),
        "args": Field(
            config=Permissive({}),
            is_required=False,
            description="Supply arguments to the macro. This dictionary will be mapped to the keyword arguments defined in the selected macro. This argument should be a dictionary, eg. {'my_variable': 'my_value'}",
        ),
    },
)
@experimental
def dbt_cli_run_operation(context) -> DbtCliResult:
    """This solid executes ``dbt run-operation`` via the dbt CLI."""
    logs, raw_output, return_code = execute_dbt(
        context.solid_config["dbt_executable"],
        command=("run-operation", context.solid_config["macro"]),
        flags_dict=passthrough_flags_only(context.solid_config, ("args",)),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
    )

    yield AssetMaterialization(
        asset_key="dbt_cli_run_operation-shell_output",  # TODO: Perhaps derive asset key from CLI flags?
        description="The output of a shell execution of `dbt run-operation`.",
        metadata_entries=[
            EventMetadataEntry.float(
                label="return_code",
                value=float(return_code),
                description="The return code of a shell exeuction of `dbt run-operation`.",
            ),
            EventMetadataEntry.text(
                label="raw_output",
                text=raw_output,
                description="The raw output of a shell execution of `dbt run-operation`.",
            ),
        ],
    )

    yield Output(DbtCliResult(logs=logs, raw_output=raw_output, return_code=return_code))


@solid(
    description="A solid to invoke dbt source snapshot-freshness via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtCliResult)],
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
            description="Specify the output path for the json report. By default, outputs to target/sources.json",
        ),
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description="Specify number of threads to use while executing models. Overrides settings in profiles.yml.",
        ),
    },
)
@experimental
def dbt_cli_snapshot_freshness(context) -> DbtCliResult:
    """This solid executes ``dbt source snapshot-freshness`` via the dbt CLI."""
    logs, raw_output, return_code = execute_dbt(
        context.solid_config["dbt_executable"],
        command=("source", "snapshot-freshness"),
        flags_dict=passthrough_flags_only(context.solid_config, ("select", "output", "threads")),
        log=context.log,
        warn_error=context.solid_config["warn-error"],
        ignore_handled_error=context.solid_config["ignore_handled_error"],
    )

    yield AssetMaterialization(
        asset_key="dbt_cli_snapshot_freshness-shell_output",  # TODO: Perhaps derive asset key from CLI flags?
        description="The output of a shell execution of `dbt source snapshot-freshness`.",
        metadata_entries=[
            EventMetadataEntry.float(
                label="return_code",
                value=float(return_code),
                description="The return code of a shell exeuction of `dbt source snapshot-freshness`.",
            ),
            EventMetadataEntry.text(
                label="raw_output",
                text=raw_output,
                description="The raw output of a shell execution of `dbt source snapshot-freshness`.",
            ),
        ],
    )

    yield Output(DbtCliResult(logs=logs, raw_output=raw_output, return_code=return_code))


@solid(
    description="A solid to invoke dbt compile via CLI.",
    input_defs=[InputDefinition(name="start_after", dagster_type=Nothing)],
    output_defs=[OutputDefinition(name="result", dagster_type=DbtCliResult)],
    config_schema={
        **CLI_CONFIG_SCHEMA,
        "parse-only": Field(config=bool, is_required=False, default_value=False,),
        "threads": Field(
            config=Noneable(int),
            default_value=None,
            is_required=False,
            description="Specify number of threads to use while executing models. Overrides settings in profiles.yml.",
        ),
        "no-version-check": Field(
            config=bool,
            description="Skip the check that dbt's version matches the one specified in the dbt_project.yml file ('require-dbt-version')",
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
            description="If set, use the given directory as the source for json files to compare with this project.",
        ),
        "full-refresh": Field(
            config=bool,
            description="If specified, DBT will drop incremental models and fully-recalculate the incremental table from the model definition. (--full-refresh)",
            is_required=False,
            default_value=False,
        ),
    },
)
@experimental
def dbt_cli_compile(context) -> DbtCliResult:
    """This solid executes ``dbt compile`` via the dbt CLI."""
    logs, raw_output, return_code = execute_dbt(
        context.solid_config["dbt_executable"],
        command=("compile",),
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
    )

    yield AssetMaterialization(
        asset_key="dbt_cli_compile-shell_output",  # TODO: Perhaps derive asset key from CLI flags?
        description="The output of a shell execution of `dbt compile`.",
        metadata_entries=[
            EventMetadataEntry.float(
                label="return_code",
                value=float(return_code),
                description="The return code of a shell exeuction of `dbt compile`.",
            ),
            EventMetadataEntry.text(
                label="raw_output",
                text=raw_output,
                description="The raw output of a shell execution of `dbt compile`.",
            ),
        ],
    )

    yield Output(DbtCliResult(logs=logs, raw_output=raw_output, return_code=return_code))
