import collections
import functools
import inspect
import os
from pathlib import Path
from typing import Any, NamedTuple, Optional, cast

import yaml
from click import Context
from dagster_shared.merger import deep_merge_dicts
from dagster_shared.utils import remove_none_recursively
from typer import Option

from . import gql, ui
from .core.errors import DagsterCloudHTTPError
from .utils import add_options

DEPLOYMENT_CLI_ARGUMENT = "deployment"
DEPLOYMENT_ENV_VAR_NAME = "DAGSTER_CLOUD_DEPLOYMENT"

ORGANIZATION_CLI_ARGUMENT = "organization"
ORGANIZATION_ENV_VAR_NAME = "DAGSTER_CLOUD_ORGANIZATION"

TOKEN_CLI_ARGUMENT = "api-token"
TOKEN_CLI_ARGUMENT_VAR = TOKEN_CLI_ARGUMENT.replace("-", "_")
TOKEN_ENV_VAR_NAME = "DAGSTER_CLOUD_API_TOKEN"

URL_CLI_ARGUMENT = "url"
URL_ENV_VAR_NAME = "DAGSTER_CLOUD_URL"

DEFAULT_CLOUD_CLI_FOLDER = os.path.join(os.path.expanduser("~"), ".dagster_cloud_cli")
DEFAULT_CLOUD_CLI_CONFIG = os.path.join(DEFAULT_CLOUD_CLI_FOLDER, "config")

LOCATION_LOAD_TIMEOUT_CLI_ARGUMENT = "location-load-timeout"
LOCATION_LOAD_TIMEOUT_ARGUMENT_VAR = LOCATION_LOAD_TIMEOUT_CLI_ARGUMENT.replace("-", "_")
LOCATION_LOAD_TIMEOUT_ENV_VAR_NAME = "DAGSTER_CLOUD_LOCATION_LOAD_TIMEOUT"
DEFAULT_LOCATION_LOAD_TIMEOUT = 3600


AGENT_HEARTBEAT_TIMEOUT_CLI_ARGUMENT = "agent-heartbeat-timeout"
AGENT_HEARTBEAT_TIMEOUT_ARGUMENT_VAR = AGENT_HEARTBEAT_TIMEOUT_CLI_ARGUMENT.replace("-", "_")
AGENT_HEARTBEAT_TIMEOUT_ENV_VAR_NAME = "DAGSTER_CLOUD_AGENT_HEARTBEAT_TIMEOUT"
DEFAULT_AGENT_HEARTBEAT_TIMEOUT = 60


class DagsterCloudCliConfig(
    NamedTuple(
        "_DagsterCloudCliConfig",
        [
            ("organization", Optional[str]),
            ("default_deployment", Optional[str]),
            ("user_token", Optional[str]),
            ("agent_timeout", Optional[int]),
        ],
    )
):
    __slots__ = ()

    def __new__(cls, **kwargs):
        none_defaults = {k: kwargs[k] if k in kwargs else None for k in cls._fields}
        return super().__new__(cls, **none_defaults)


def get_config_path():
    return os.getenv("DAGSTER_CLOUD_CLI_CONFIG", DEFAULT_CLOUD_CLI_CONFIG)


def write_config(config: DagsterCloudCliConfig):
    """Writes the given config object to the CLI config file."""
    config_path = get_config_path()
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf8") as f:
        config_dict = {k: v for k, v in config._asdict().items() if v is not None}
        f.write(yaml.dump(config_dict))


def read_config() -> DagsterCloudCliConfig:
    """Reads the CLI config file into a config object."""
    config_path = get_config_path()
    if not os.path.isfile(config_path):
        return DagsterCloudCliConfig()

    with open(config_path, encoding="utf8") as f:
        raw_in = yaml.load(f.read(), Loader=yaml.SafeLoader)
        return DagsterCloudCliConfig(**raw_in)


def get_deployment(ctx: Optional[Context] = None) -> Optional[str]:
    """Gets the configured deployment to target.
    Highest precedence is a deployment argument, then `DAGSTER_CLOUD_DEPLOYMENT`
    env var, then `~/.dagster_cloud_cli/config` default.
    """
    if ctx and ctx.params.get(DEPLOYMENT_CLI_ARGUMENT):
        return ctx.params[DEPLOYMENT_CLI_ARGUMENT]
    return os.getenv(DEPLOYMENT_ENV_VAR_NAME, read_config().default_deployment)


def get_organization(ctx: Optional[Context] = None) -> Optional[str]:
    """Gets the configured organization to target.
    Highest precedence is an organization argument, then `DAGSTER_CLOUD_ORGANIZATION`
    env var, then `~/.dagster_cloud_cli/config` value.
    """
    if ctx and ctx.params.get(ORGANIZATION_CLI_ARGUMENT):
        return ctx.params[ORGANIZATION_CLI_ARGUMENT]
    return os.getenv(ORGANIZATION_ENV_VAR_NAME, read_config().organization)


def get_location_load_timeout() -> int:
    """Gets the configured location load timeout to target.
    Highest precedence is an location-load-timeout argument, then `DAGTER_CLOUD_LOCATION_LOAD_TIMEOUT`
    env var, then `~/.dagster_cloud_cli/config` value.
    """
    config_timeout = read_config().agent_timeout
    default_timeout = (
        config_timeout if config_timeout is not None else DEFAULT_LOCATION_LOAD_TIMEOUT
    )
    assert default_timeout is not None

    env_val = os.getenv(LOCATION_LOAD_TIMEOUT_ENV_VAR_NAME)

    return int(cast(str, env_val)) if env_val is not None else default_timeout


def get_agent_heartbeat_timeout() -> int:
    """Gets the configured agent timeout to target.
    Highest precedence is an agent-timeout argument, then `DAGTER_CLOUD_AGENT_HEARTBEAT_TIMEOUT`
    env var.
    """
    default_timeout = DEFAULT_AGENT_HEARTBEAT_TIMEOUT
    env_val = os.getenv(AGENT_HEARTBEAT_TIMEOUT_ENV_VAR_NAME)

    return int(cast(str, env_val)) if env_val is not None else default_timeout


def get_user_token(ctx: Optional[Context] = None) -> Optional[str]:
    """Gets the configured user token to use.
    Highest precedence is an api-token argument, then `DAGSTER_CLOUD_API_TOKEN`
    env var, then `~/.dagster_cloud_cli/config` value.
    """
    if ctx and ctx.params.get(TOKEN_CLI_ARGUMENT_VAR):
        return ctx.params[TOKEN_CLI_ARGUMENT_VAR]
    return os.getenv(TOKEN_ENV_VAR_NAME, read_config().user_token)


def available_deployment_names(ctx, incomplete: str = "") -> list[str]:
    """Gets a list of deployment names given the Typer Context, used for CLI completion."""
    organization = get_organization(ctx=ctx)
    user_token = get_user_token(ctx=ctx)

    if not organization or not user_token:
        return []
    try:
        with gql.graphql_client_from_url(gql.url_from_config(organization), user_token) as client:
            deployments = gql.fetch_full_deployments(client)
        names = [deployment["deploymentName"] for deployment in deployments]
        return [name for name in names if name.startswith(incomplete)]
    except DagsterCloudHTTPError:
        return []


def get_url(ctx: Optional[Context] = None) -> Optional[str]:
    """Gets the url passed in or from the environment."""
    if ctx and ctx.params.get(URL_CLI_ARGUMENT):
        return ctx.params[URL_CLI_ARGUMENT]
    return os.getenv(URL_ENV_VAR_NAME)


def get_org_url(organization: str, dagster_env: Optional[str]):
    if dagster_env:
        return f"https://{organization}.{dagster_env}.dagster.cloud"
    return f"https://{organization}.dagster.cloud"


# Typer Option definitions for common CLI config options (organization, deployment, user token)
ORGANIZATION_OPTION = Option(
    get_organization,
    "--organization",
    "-o",
    help="Organization to target.",
    show_default=get_organization(),  # type: ignore
)
DEPLOYMENT_OPTION = Option(
    get_deployment,
    "--deployment",
    "-d",
    help="Deployment to target.",
    autocompletion=available_deployment_names,
    show_default=get_deployment(),  # type: ignore
)

DAGSTER_ENV_OPTION = Option(
    None,
    "--dagster-env",
    hidden=True,
    envvar="DAGSTER_CLOUD_ENV",
)

USER_TOKEN_OPTION = Option(
    get_user_token,
    "--api-token",
    "--user-token",
    "-u",
    help="Cloud user token.",
    show_default=ui.censor_token(get_user_token()) if get_user_token() else None,  # type: ignore
)
URL_OPTION = Option(
    get_url,
    "--url",
    help=(
        "[DEPRECATED] Your Dagster Cloud url, in the form of"
        " 'https://{ORGANIZATION_NAME}.dagster.cloud/{DEPLOYMENT_NAME}'."
    ),
    hidden=True,
)

LOCATION_LOAD_TIMEOUT_OPTION = Option(
    get_location_load_timeout(),
    f"--{LOCATION_LOAD_TIMEOUT_CLI_ARGUMENT}",
    "--agent-timeout",
    help=(
        "After making changes to the workspace. how long in seconds to wait for the location to"
        " load before timing out with an error"
    ),
)

AGENT_HEARTBEAT_TIMEOUT_OPTION = Option(
    get_agent_heartbeat_timeout(),
    f"--{AGENT_HEARTBEAT_TIMEOUT_CLI_ARGUMENT}",
    "--agent-timeout",
    help=(
        "After making changes to the workspace. how long in seconds to wait for the agent to"
        " heartbeat before timing out with an error"
    ),
)


def dagster_cloud_options(
    allow_empty: bool = False,
    allow_empty_deployment: bool = False,
    requires_url: bool = False,
):
    """Apply this decorator to Typer commands to make them take the
    `organization`, `deployment`, and `api-token` arguments.
    These values are passed as keyword arguments.

    Unless `allow_empty` or `allow_empty_deployment` are set, an error
    will be raised if these values are not specified as arguments or via config/env var.

    Set `requires_url` if the command needs a Dagster webserver url; if so, this will be provided
    via the `url` keyword argument.
    """

    def decorator(to_wrap):
        wrapped_sig = inspect.signature(to_wrap)
        params = collections.OrderedDict(wrapped_sig.parameters)

        options = {
            ORGANIZATION_CLI_ARGUMENT: (str, ORGANIZATION_OPTION),
            TOKEN_CLI_ARGUMENT_VAR: (str, USER_TOKEN_OPTION),
        }

        # For requests that need a graphql client, a user can supply a URL (though this
        # is a hidden option), or an organization and deployment
        if requires_url:
            options[URL_CLI_ARGUMENT] = (str, URL_OPTION)

        has_deployment_param = (
            DEPLOYMENT_CLI_ARGUMENT in params
            and params[DEPLOYMENT_CLI_ARGUMENT].default is params[DEPLOYMENT_CLI_ARGUMENT].empty
        ) or requires_url
        if has_deployment_param:
            options[DEPLOYMENT_CLI_ARGUMENT] = (str, DEPLOYMENT_OPTION)

        has_location_load_timeout_param = LOCATION_LOAD_TIMEOUT_ARGUMENT_VAR in params
        if has_location_load_timeout_param:
            options[LOCATION_LOAD_TIMEOUT_ARGUMENT_VAR] = (int, LOCATION_LOAD_TIMEOUT_OPTION)  # pyright: ignore[reportArgumentType]
        has_agent_heartbeat_timeout_param = AGENT_HEARTBEAT_TIMEOUT_ARGUMENT_VAR in params
        if has_agent_heartbeat_timeout_param:
            options[AGENT_HEARTBEAT_TIMEOUT_ARGUMENT_VAR] = (int, AGENT_HEARTBEAT_TIMEOUT_OPTION)  # pyright: ignore[reportArgumentType]

        with_options = add_options(options)(to_wrap)

        @functools.wraps(with_options)
        def wrap_function(*args, **kwargs):
            # If underlying command needs a URL and none is explicitly provided,
            # generate one from the organization + deployment
            if (
                requires_url
                and not kwargs.get(URL_CLI_ARGUMENT)
                and kwargs.get(ORGANIZATION_CLI_ARGUMENT)
                and kwargs.get(DEPLOYMENT_CLI_ARGUMENT)
            ):
                kwargs[URL_CLI_ARGUMENT] = gql.url_from_config(
                    organization=kwargs.get(ORGANIZATION_CLI_ARGUMENT),  # pyright: ignore[reportArgumentType]
                    deployment=kwargs.get(DEPLOYMENT_CLI_ARGUMENT),
                )

            lacking_url = requires_url and not kwargs.get(URL_CLI_ARGUMENT)

            # Raise errors if important options are not provided
            if not kwargs.get(TOKEN_CLI_ARGUMENT_VAR) and (not allow_empty or lacking_url):
                raise ui.error(
                    "A Dagster Cloud user token must be specified for this command.\n\nYou may"
                    " specify a token by:\n- Providing the"
                    f" {ui.as_code('--' + TOKEN_CLI_ARGUMENT)} parameter.\n- Setting the"
                    f" {ui.as_code(TOKEN_ENV_VAR_NAME)} environment variable.\n- Specifying"
                    f" {ui.as_code('user_token')} in your config file ({get_config_path()}), run"
                    f" {ui.as_code('dagster-cloud config setup')}."
                )
            if not kwargs.get(ORGANIZATION_CLI_ARGUMENT) and (not allow_empty or lacking_url):
                raise ui.error(
                    "A Dagster Cloud organization must be specified for this command.\n\nYou may"
                    " specify your organization by:\n- Providing the"
                    f" {ui.as_code('--' + ORGANIZATION_CLI_ARGUMENT)} parameter.\n- Setting the"
                    f" {ui.as_code(ORGANIZATION_ENV_VAR_NAME)} environment variable.\n- Specifying"
                    f" {ui.as_code('organization')} in your config file ({get_config_path()}), run"
                    f" {ui.as_code('dagster-cloud config setup')}."
                )
            if (
                DEPLOYMENT_CLI_ARGUMENT in kwargs
                and not kwargs.get(DEPLOYMENT_CLI_ARGUMENT)
                and (not (allow_empty or allow_empty_deployment) or lacking_url)
            ):
                raise ui.error(
                    "A Dagster Cloud deployment must be specified for this command.\n\nYou may"
                    " specify a deployment by:\n- Providing the"
                    f" {ui.as_code('--' + DEPLOYMENT_CLI_ARGUMENT)} parameter.\n- Setting the"
                    f" {ui.as_code(DEPLOYMENT_ENV_VAR_NAME)} environment variable.\n- Running"
                    f" {ui.as_code('dagster-cloud config set-deployment <deployment_name>')}.\n-"
                    f" Specifying {ui.as_code('default_deployment')} in your config file"
                    f" ({get_config_path()})."
                )

            new_kwargs = dict(kwargs)
            with_options(*args, **new_kwargs)

        return wrap_function

    return decorator


DEPLOYMENT_METADATA_OPTIONS = {
    # Options to specify code location metadata inline
    "image": (str, Option(None, "--image", help="Docker image.")),
    "location_name": (str, Option(None, "--location-name", help="Location name.")),
    "python_file": (
        Path,
        Option(
            None, "--python-file", "-f", exists=False, help="Python file where repository lives."
        ),
    ),
    "working_directory": (
        str,
        Option(
            None,
            "--working-directory",
            "-d",
            help="Base directory to use for local imports when loading the repositories.",
        ),
    ),
    "package_name": (
        str,
        Option(
            None,
            "--package-name",
            "-p",
            help="Local or installed Python package where repositories live",
        ),
    ),
    "module_name": (
        str,
        Option(None, "--module-name", "-m", help="Python module where repositories live"),
    ),
    "executable_path": (
        str,
        Option(
            None,
            "--executable-path",
            help=(
                "Path to reach the executable to use for the Python environment to load the"
                " repositories. Defaults to the installed `dagster` command-line entry point."
            ),
        ),
    ),
    "attribute": (
        str,
        Option(
            None,
            "--attribute",
            "-a",
            help=(
                "Optional attribute that is either a repository or a function that returns a"
                " repository."
            ),
        ),
    ),
    "commit_hash": (
        str,
        Option(
            None,
            "--commit-hash",
            help="Optional metadata which indicates the commit sha associated with this location.",
        ),
    ),
    "git_url": (
        str,
        Option(
            None,
            "--git-url",
            help=(
                "Optional metadata which specifies a source code reference link for this location."
            ),
        ),
    ),
}


LOCATION_FILE_OPTIONS = {
    # Specify code location metadata via file
    "location_file": (
        Path,
        Option(
            None,
            "--location-file",
            "--from",
            exists=True,
            help="YAML file specifying code location metadata.",
        ),
    ),
}
DEPLOYMENT_CLI_OPTIONS = {
    **DEPLOYMENT_METADATA_OPTIONS,
    **LOCATION_FILE_OPTIONS,
}


def get_location_document(name: Optional[str], kwargs: dict[str, Any]) -> dict[str, Any]:
    name = name or kwargs.get("location_name")
    location_file = kwargs.get("location_file")
    location_doc_from_file = {}
    if location_file:
        with open(location_file, encoding="utf8") as f:
            location_doc_from_file = yaml.safe_load(f.read())

    if not location_file and not name:
        raise ui.error(
            "No location name provided. You must either provide a location file with the"
            f" {ui.as_code('--location-file/--from')} flag or specify the location name as an"
            " argument."
        )
    elif location_file:
        if "locations" in location_doc_from_file:
            if not name:
                raise ui.error(
                    "If specifying a file with multiple locations, must specify a location name."
                )
            locations_by_name = {
                loc["location_name"]: loc for loc in location_doc_from_file["locations"]
            }
            if name not in locations_by_name:
                raise ui.error(f"No location with name {name} defined in location file.")
            location_doc_from_file = locations_by_name[name]
        elif (
            name
            and location_doc_from_file.get("location_name")
            and location_doc_from_file["location_name"] != name
        ):
            raise ui.error(
                f"Name provided via argument and in location file does not match, {name} =/="
                f" {location_doc_from_file['location_name']}."
            )

    python_file = kwargs.get("python_file")
    python_file_str = str(python_file) if python_file else None

    if "build" in location_doc_from_file:
        del location_doc_from_file["build"]

    location_doc_from_kwargs = remove_none_recursively(
        {
            "location_name": name,
            "code_source": {
                "python_file": python_file_str,
                "module_name": kwargs.get("module_name"),
                "package_name": kwargs.get("package_name"),
            },
            "working_directory": kwargs.get("working_directory"),
            "image": kwargs.get("image"),
            "executable_path": kwargs.get("executable_path"),
            "attribute": kwargs.get("attribute"),
            "git": {"commit_hash": kwargs.get("commit_hash"), "url": kwargs.get("git_url")},
            "pex_metadata": (
                {"pex_tag": kwargs["pex_tag"], "python_version": kwargs.get("python_version")}
                if kwargs.get("pex_tag")
                else None
            ),
        }
    )
    return deep_merge_dicts(location_doc_from_file, location_doc_from_kwargs)
