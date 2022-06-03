from dagster import Field, Permissive, StringSource

DEFAULT_DBT_EXECUTABLE = "dbt"
DEFAULT_DBT_TARGET_PATH = "target"

# The set of dbt cli commands that result in the creation of a run_results.json output file
# https://docs.getdbt.com/reference/artifacts/run-results-json
DBT_RUN_RESULTS_COMMANDS = ["run", "test", "seed", "snapshot", "docs generate", "build"]

# The following config fields correspond to flags that apply to all dbt CLI commands. For details
# on dbt CLI flags, see
# https://github.com/fishtown-analytics/dbt/blob/1f8e29276e910c697588c43f08bc881379fff178/core/dbt/main.py#L260-L329
CLI_COMMON_FLAGS_CONFIG_SCHEMA = {
    "project-dir": Field(
        config=StringSource,
        is_required=False,
        description=(
            "Which directory to look in for the dbt_project.yml file. Default is the current "
            "working directory and its parents."
        ),
        default_value=".",
    ),
    "profiles-dir": Field(
        config=StringSource,
        is_required=False,
        description=(
            "Which directory to look in for the profiles.yml file. Default = $DBT_PROFILES_DIR or "
            "$HOME/.dbt"
        ),
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
        description=(
            "Supply variables to the project. This argument overrides variables defined in your "
            "dbt_project.yml file. This argument should be a dictionary, eg. "
            "{'my_variable': 'my_value'}"
        ),
    ),
    "bypass-cache": Field(
        config=bool,
        is_required=False,
        description="If set, bypass the adapter-level cache of database state",
        default_value=False,
    ),
}

# The following config fields correspond to options that apply to all CLI solids, but should not be
# formatted as CLI flags.
CLI_COMMON_OPTIONS_CONFIG_SCHEMA = {
    "warn-error": Field(
        config=bool,
        is_required=False,
        description=(
            "If dbt would normally warn, instead raise an exception. Examples include --models "
            "that selects nothing, deprecations, configurations with no associated models, "
            "invalid test configurations, and missing sources/refs in tests."
        ),
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
        description=(
            "When True, will not raise an exception when the dbt CLI returns error code 1. "
            "Default is False."
        ),
        default_value=False,
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
    "docs_url": Field(
        config=StringSource,
        is_required=False,
        description="The url for where dbt docs are being served for this project.",
    ),
}
