import os
import re
import shutil
import uuid
from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from functools import cache, cached_property
from pathlib import Path
from subprocess import check_output
from typing import Any, Optional, Union, cast

import yaml
from dagster import (
    AssetExecutionContext,
    ConfigurableResource,
    OpExecutionContext,
    get_dagster_logger,
)
from dagster._annotations import public
from dagster._core.execution.context.init import InitResourceContext
from dagster._utils import pushd
from packaging import version
from pydantic import Field, ValidationInfo, field_validator, model_validator

from dagster_dbt.asset_utils import (
    DBT_INDIRECT_SELECTION_ENV,
    get_updated_cli_invocation_params_for_context,
)
from dagster_dbt.compat import DBT_PYTHON_VERSION, BaseAdapter
from dagster_dbt.core.dbt_cli_invocation import DbtCliInvocation, _get_dbt_target_path
from dagster_dbt.dagster_dbt_translator import DagsterDbtTranslator, validate_opt_translator
from dagster_dbt.dbt_manifest import DbtManifestParam, validate_manifest
from dagster_dbt.dbt_project import DbtProject

logger = get_dagster_logger()


@cache
def _get_dbt_executable() -> str:
    if shutil.which("dbtf"):
        return "dbtf"
    else:
        return "dbt"


DBT_EXECUTABLE = _get_dbt_executable()
DBT_PROJECT_YML_NAME = "dbt_project.yml"
DBT_PROFILES_YML_NAME = "profiles.yml"


DAGSTER_GITHUB_REPO_DBT_PACKAGE = "https://github.com/dagster-io/dagster.git"


def _dbt_packages_has_dagster_dbt(packages_file: Path) -> bool:
    """Checks whether any package in the passed yaml file is the Dagster dbt package."""
    packages = cast(
        "list[dict[str, Any]]", yaml.safe_load(packages_file.read_text()).get("packages", [])
    )
    return any(package.get("git") == DAGSTER_GITHUB_REPO_DBT_PACKAGE for package in packages)


class DbtCliResource(ConfigurableResource):
    """A resource used to execute dbt CLI commands.

    Args:
        project_dir (str): The path to the dbt project directory. This directory should contain a
            `dbt_project.yml`. See https://docs.getdbt.com/reference/dbt_project.yml for more
            information.
        global_config_flags (List[str]): A list of global flags configuration to pass to the dbt CLI
            invocation. Invoke `dbt --help` to see a full list of global flags.
        profiles_dir (Optional[str]): The path to the directory containing your dbt `profiles.yml`.
            By default, the current working directory is used, which is the dbt project directory.
            See https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        profile (Optional[str]): The profile from your dbt `profiles.yml` to use for execution. See
            https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        target (Optional[str]): The target from your dbt `profiles.yml` to use for execution. See
            https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more
            information.
        dbt_executable (str): The path to the dbt executable. By default, this is `dbt`.
        state_path (Optional[str]): The path, relative to the project directory, to a directory of
            dbt artifacts to be used with `--state` / `--defer-state`.

    Examples:
        Creating a dbt resource with only a reference to ``project_dir``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(project_dir="/path/to/dbt/project")

        Creating a dbt resource with a custom ``profiles_dir``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                profiles_dir="/path/to/dbt/project/profiles",
            )

        Creating a dbt resource with a custom ``profile`` and ``target``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                profiles_dir="/path/to/dbt/project/profiles",
                profile="jaffle_shop",
                target="dev",
            )

        Creating a dbt resource with global configs, e.g. disabling colored logs with ``--no-use-color``:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                global_config_flags=["--no-use-color"],
            )

        Creating a dbt resource with custom dbt executable path:

        .. code-block:: python

            from dagster_dbt import DbtCliResource

            dbt = DbtCliResource(
                project_dir="/path/to/dbt/project",
                dbt_executable="/path/to/dbt/executable",
            )
    """

    project_dir: str = Field(
        description=(
            "The path to your dbt project directory. This directory should contain a"
            " `dbt_project.yml`. See https://docs.getdbt.com/reference/dbt_project.yml for more"
            " information."
        ),
    )
    global_config_flags: list[str] = Field(
        default=[],
        description=(
            "A list of global flags configuration to pass to the dbt CLI invocation. See"
            " https://docs.getdbt.com/reference/global-configs for a full list of configuration."
        ),
    )
    profiles_dir: Optional[str] = Field(
        default=None,
        description=(
            "The path to the directory containing your dbt `profiles.yml`. By default, the current"
            " working directory is used, which is the dbt project directory."
            " See https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for "
            " more information."
        ),
    )
    profile: Optional[str] = Field(
        default=None,
        description=(
            "The profile from your dbt `profiles.yml` to use for execution. See"
            " https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more"
            " information."
        ),
    )
    target: Optional[str] = Field(
        default=None,
        description=(
            "The target from your dbt `profiles.yml` to use for execution. See"
            " https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles for more"
            " information."
        ),
    )
    dbt_executable: str = Field(
        default=DBT_EXECUTABLE,
        description="The path to the dbt executable. Defaults to `dbtf` if available, otherwise `dbt`.",
    )
    state_path: Optional[str] = Field(
        default=None,
        description=(
            "The path, relative to the project directory, to a directory of dbt artifacts to be"
            " used with --state / --defer-state."
            " This can be used with methods such as get_defer_args to allow for a @dbt_assets to"
            " use defer in the appropriate environments."
        ),
    )

    def __init__(
        self,
        project_dir: Union[str, Path, DbtProject],
        global_config_flags: Optional[list[str]] = None,
        profiles_dir: Optional[Union[str, Path]] = None,
        profile: Optional[str] = None,
        target: Optional[str] = None,
        dbt_executable: Union[str, Path] = DBT_EXECUTABLE,
        state_path: Optional[Union[str, Path]] = None,
        **kwargs,  # allow custom subclasses to add fields
    ):
        if isinstance(project_dir, DbtProject):
            if not state_path and project_dir.state_path:
                state_path = project_dir.state_path

            if not profiles_dir and project_dir.profiles_dir:
                profiles_dir = project_dir.profiles_dir

            if not profile and project_dir.profile:
                profile = project_dir.profile

            if not target and project_dir.target:
                target = project_dir.target

            project_dir = project_dir.project_dir

        # DbtProject handles making state_path relative to project_dir
        # when directly instantiated we have to join it
        elif state_path and not Path(state_path).is_absolute():
            state_path = os.path.join(project_dir, state_path)

        project_dir = os.fspath(project_dir)
        state_path = state_path and os.fspath(state_path)

        # static typing doesn't understand whats going on here, thinks these fields dont exist
        super().__init__(
            project_dir=project_dir,  # type: ignore
            global_config_flags=global_config_flags or [],  # type: ignore
            profiles_dir=profiles_dir,  # type: ignore
            profile=profile,  # type: ignore
            target=target,  # type: ignore
            dbt_executable=dbt_executable,  # type: ignore
            state_path=state_path,  # type: ignore
            **kwargs,
        )

    @classmethod
    def _validate_absolute_path_exists(cls, path: Union[str, Path]) -> Path:
        absolute_path = Path(path).absolute()
        try:
            resolved_path = absolute_path.resolve(strict=True)
        except FileNotFoundError:
            raise ValueError(f"The absolute path of '{path}' ('{absolute_path}') does not exist")

        return resolved_path

    @classmethod
    def _validate_path_contains_file(cls, path: Path, file_name: str, error_message: str):
        if not path.joinpath(file_name).exists():
            raise ValueError(error_message)

    @field_validator("project_dir", "profiles_dir", "dbt_executable", mode="before")
    def convert_path_to_str(cls, v: Any) -> Any:
        """Validate that the path is converted to a string."""
        if isinstance(v, Path):
            resolved_path = cls._validate_absolute_path_exists(v)

            absolute_path = Path(v).absolute()
            try:
                resolved_path = absolute_path.resolve(strict=True)
            except FileNotFoundError:
                raise ValueError(f"The absolute path of '{v}' ('{absolute_path}') does not exist")
            return os.fspath(resolved_path)

        return v

    @field_validator("project_dir")
    def validate_project_dir(cls, project_dir: str) -> str:
        resolved_project_dir = cls._validate_absolute_path_exists(project_dir)

        cls._validate_path_contains_file(
            path=resolved_project_dir,
            file_name=DBT_PROJECT_YML_NAME,
            error_message=(
                f"{resolved_project_dir} does not contain a {DBT_PROJECT_YML_NAME} file. Please"
                " specify a valid path to a dbt project."
            ),
        )

        return os.fspath(resolved_project_dir)

    @field_validator("profiles_dir")
    def validate_profiles_dir(cls, profiles_dir: Optional[str]) -> Optional[str]:
        if profiles_dir is None:
            return None

        resolved_profiles_dir = cls._validate_absolute_path_exists(profiles_dir)

        cls._validate_path_contains_file(
            path=resolved_profiles_dir,
            file_name=DBT_PROFILES_YML_NAME,
            error_message=(
                f"{resolved_profiles_dir} does not contain a {DBT_PROFILES_YML_NAME} file. Please"
                " specify a valid path to a dbt profile directory."
            ),
        )

        return os.fspath(resolved_profiles_dir)

    @field_validator("dbt_executable")
    def validate_dbt_executable(cls, dbt_executable: str) -> str:
        resolved_dbt_executable = shutil.which(dbt_executable)
        if not resolved_dbt_executable:
            raise ValueError(
                f"The dbt executable '{dbt_executable}' does not exist. Please specify a valid"
                " path to a dbt executable."
            )

        return dbt_executable

    @model_validator(mode="before")
    def validate_dbt_version(cls, values: dict[str, Any]) -> dict[str, Any]:
        """Validate that the dbt version is supported."""
        if DBT_PYTHON_VERSION is None:
            # dbt-core is not installed, so assume fusion is installed
            return values

        if DBT_PYTHON_VERSION < version.parse("1.7.0"):
            raise ValueError(
                "To use `dagster_dbt.DbtCliResource`, you must use `dbt-core>=1.7.0` or dbt Fusion. Currently,"
                f" you are using `dbt-core=={DBT_PYTHON_VERSION.base_version}`. Please install a compatible dbt engine."
            )

        return values

    @field_validator("state_path")
    def validate_state_path(cls, state_path: Optional[str], info: ValidationInfo) -> Optional[str]:
        if state_path is None:
            return None

        return os.fspath(Path(state_path).absolute().resolve())

    def _get_unique_target_path(
        self, *, context: Optional[Union[OpExecutionContext, AssetExecutionContext]]
    ) -> Path:
        """Get a unique target path for the dbt CLI invocation.

        Args:
            context (Optional[Union[OpExecutionContext, AssetExecutionContext]]): The execution context.

        Returns:
            str: A unique target path for the dbt CLI invocation.
        """
        unique_id = str(uuid.uuid4())[:7]
        path = unique_id
        if context:
            path = f"{context.op_execution_context.op.name}-{context.run.run_id[:7]}-{unique_id}"

        current_target_path = _get_dbt_target_path()

        return current_target_path.joinpath(path)

    def _initialize_dbt_core_adapter(self, args: Sequence[str]) -> BaseAdapter:
        from dbt.adapters.factory import get_adapter, register_adapter, reset_adapters
        from dbt.config import RuntimeConfig
        from dbt.config.runtime import load_profile, load_project
        from dbt.config.utils import parse_cli_vars
        from dbt.flags import get_flags, set_from_args

        parser = ArgumentParser(description="Parse cli vars from dbt command")
        parser.add_argument("--vars")
        var_args, _ = parser.parse_known_args(args)
        if not var_args.vars:
            cli_vars = {}
        else:
            cli_vars = parse_cli_vars(var_args.vars)

        if DBT_PYTHON_VERSION >= version.parse("1.8.0"):
            from dbt_common.context import set_invocation_context

            set_invocation_context(os.environ.copy())

        # constructs a dummy set of flags, using the `run` command (ensures profile/project reqs get loaded)
        profiles_dir = self.profiles_dir if self.profiles_dir else self.project_dir
        set_from_args(Namespace(profiles_dir=profiles_dir), None)
        flags = get_flags()

        profile = load_profile(self.project_dir, cli_vars, self.profile, self.target)
        project = load_project(self.project_dir, False, profile, cli_vars)
        config = RuntimeConfig.from_parts(project, profile, flags)

        # these flags are required for the adapter to be able to look up
        # relations correctly
        new_flags = Namespace()
        for key, val in config.args.__dict__.items():
            setattr(new_flags, key, val)

        setattr(new_flags, "profile", profile.profile_name)
        setattr(new_flags, "target", profile.target_name)
        config.args = new_flags

        # If the dbt adapter is DuckDB, set the access mode to READ_ONLY, since DuckDB only allows
        # simultaneous connections for read-only access.

        if config.credentials and config.credentials.__class__.__name__ == "DuckDBCredentials":
            from dbt.adapters.duckdb.credentials import DuckDBCredentials

            if isinstance(config.credentials, DuckDBCredentials):
                if not config.credentials.config_options:
                    config.credentials.config_options = {}
                config.credentials.config_options["access_mode"] = "READ_ONLY"
                # convert adapter duckdb filepath to absolute path, since the Python
                # working directory may not be the same as the dbt project directory
                with pushd(self.project_dir):
                    config.credentials.path = os.fspath(Path(config.credentials.path).absolute())

        if DBT_PYTHON_VERSION < version.parse("1.8.0"):
            from dbt.events.functions import cleanup_event_logger  # type: ignore
        else:
            from dbt_common.events.event_manager_client import cleanup_event_logger

        cleanup_event_logger()

        # reset adapters list in case we have instantiated an adapter before in this process
        reset_adapters()
        if DBT_PYTHON_VERSION < version.parse("1.8.0"):
            register_adapter(config)  # type: ignore
        else:
            from dbt.adapters.protocol import MacroContextGeneratorCallable  # noqa: TC002
            from dbt.context.providers import generate_runtime_macro_context
            from dbt.mp_context import get_mp_context
            from dbt.parser.manifest import ManifestLoader

            register_adapter(config, get_mp_context())
            adapter = get_adapter(config)
            manifest = ManifestLoader.load_macros(
                config,
                adapter.connections.set_query_header,
                base_macros_only=True,
            )
            adapter.set_macro_resolver(manifest)
            adapter.set_macro_context_generator(
                cast("MacroContextGeneratorCallable", generate_runtime_macro_context)
            )

        adapter = cast("BaseAdapter", get_adapter(config))

        return adapter

    @cached_property
    def _cli_version(self) -> version.Version:
        """Gets the version of the currently-installed dbt executable.

        This may differ from the version of the dbt-core package, most obviously if dbt-core is not
        installed due to the fusion engine being used.
        """
        raw_output = check_output([self.dbt_executable, "--version"]).decode("utf-8").strip()
        match = re.search(r"(\d+\.\d+\.\d+)", raw_output)
        if not match:
            raise ValueError(f"Could not parse dbt version from output: {raw_output}")
        return version.parse(match.group(1))

    @public
    def get_defer_args(self) -> Sequence[str]:
        """Build the defer arguments for the dbt CLI command, using the supplied state directory.
        If no state directory is supplied, or the state directory does not have a manifest for.
        comparison, an empty list of arguments is returned.

        Returns:
            Sequence[str]: The defer arguments for the dbt CLI command.
        """
        if not (self.state_path and Path(self.state_path).joinpath("manifest.json").exists()):
            return []

        return ["--defer", "--defer-state", self.state_path]

    @public
    def get_state_args(self) -> Sequence[str]:
        """Build the state arguments for the dbt CLI command, using the supplied state directory.
        If no state directory is supplied, or the state directory does not have a manifest for.
        comparison, an empty list of arguments is returned.

        Returns:
            Sequence[str]: The state arguments for the dbt CLI command.
        """
        if not (self.state_path and Path(self.state_path).joinpath("manifest.json").exists()):
            return []

        return ["--state", self.state_path]

    @public
    def cli(
        self,
        args: Sequence[str],
        *,
        raise_on_error: bool = True,
        manifest: Optional[DbtManifestParam] = None,
        dagster_dbt_translator: Optional[DagsterDbtTranslator] = None,
        context: Optional[Union[OpExecutionContext, AssetExecutionContext]] = None,
        target_path: Optional[Path] = None,
    ) -> DbtCliInvocation:
        """Create a subprocess to execute a dbt CLI command.

        Args:
            args (Sequence[str]): The dbt CLI command to execute.
            raise_on_error (bool): Whether to raise an exception if the dbt CLI command fails.
            manifest (Optional[Union[Mapping[str, Any], str, Path]]): The dbt manifest blob. If an
                execution context from within `@dbt_assets` is provided to the context argument,
                then the manifest provided to `@dbt_assets` will be used.
            dagster_dbt_translator (Optional[DagsterDbtTranslator]): The translator to link dbt
                nodes to Dagster assets. If an execution context from within `@dbt_assets` is
                provided to the context argument, then the dagster_dbt_translator provided to
                `@dbt_assets` will be used.
            context (Optional[Union[OpExecutionContext, AssetExecutionContext]]): The execution context from within `@dbt_assets`.
                If an AssetExecutionContext is passed, its underlying OpExecutionContext will be used.
            target_path (Optional[Path]): An explicit path to a target folder to use to store and
                retrieve dbt artifacts when running a dbt CLI command. If not provided, a unique
                target path will be generated.

        Returns:
            DbtCliInvocation: A invocation instance that can be used to retrieve the output of the
                dbt CLI command.

        Examples:
            Streaming Dagster events for dbt asset materializations and observations:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    yield from dbt.cli(["run"], context=context).stream()

            Retrieving a dbt artifact after streaming the Dagster events:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    dbt_run_invocation = dbt.cli(["run"], context=context)

                    yield from dbt_run_invocation.stream()

                    # Retrieve the `run_results.json` dbt artifact as a dictionary:
                    run_results_json = dbt_run_invocation.get_artifact("run_results.json")

                    # Retrieve the `run_results.json` dbt artifact as a file path:
                    run_results_path = dbt_run_invocation.target_path.joinpath("run_results.json")

            Customizing the asset materialization metadata when streaming the Dagster events:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    dbt_cli_invocation = dbt.cli(["run"], context=context)

                    for dagster_event in dbt_cli_invocation.stream():
                        if isinstance(dagster_event, Output):
                            context.add_output_metadata(
                                metadata={
                                    "my_custom_metadata": "my_custom_metadata_value",
                                },
                                output_name=dagster_event.output_name,
                            )

                        yield dagster_event

            Suppressing exceptions from a dbt CLI command when a non-zero exit code is returned:

            .. code-block:: python

                from pathlib import Path

                from dagster import AssetExecutionContext
                from dagster_dbt import DbtCliResource, dbt_assets


                @dbt_assets(manifest=Path("target", "manifest.json"))
                def my_dbt_assets(context: AssetExecutionContext, dbt: DbtCliResource):
                    dbt_run_invocation = dbt.cli(["run"], context=context, raise_on_error=False)

                    if dbt_run_invocation.is_successful():
                        yield from dbt_run_invocation.stream()
                    else:
                        ...

            Invoking a dbt CLI command in a custom asset or op:

            .. code-block:: python

                import json

                from dagster import Nothing, Out, asset, op
                from dagster_dbt import DbtCliResource


                @asset
                def my_dbt_asset(dbt: DbtCliResource):
                    dbt_macro_args = {"key": "value"}
                    dbt.cli(["run-operation", "my-macro", json.dumps(dbt_macro_args)]).wait()


                @op(out=Out(Nothing))
                def my_dbt_op(dbt: DbtCliResource):
                    dbt_macro_args = {"key": "value"}
                    yield from dbt.cli(["run-operation", "my-macro", json.dumps(dbt_macro_args)]).stream()
        """
        dagster_dbt_translator = validate_opt_translator(dagster_dbt_translator)
        dagster_dbt_translator = dagster_dbt_translator or DagsterDbtTranslator()
        manifest = validate_manifest(manifest) if manifest else {}

        updated_params = get_updated_cli_invocation_params_for_context(
            context=context, manifest=manifest, dagster_dbt_translator=dagster_dbt_translator
        )
        manifest = updated_params.manifest
        dagster_dbt_translator = updated_params.dagster_dbt_translator
        selection_args = updated_params.selection_args
        indirect_selection = updated_params.indirect_selection
        target_path = target_path or self._get_unique_target_path(context=context)
        project_dir = Path(
            updated_params.dbt_project.project_dir
            if updated_params.dbt_project
            else self.project_dir
        )
        env = {
            # Allow IO streaming when running in Windows.
            # Also, allow it to be overriden by the current environment.
            "PYTHONLEGACYWINDOWSSTDIO": "1",
            # Pass the current environment variables to the dbt CLI invocation.
            **os.environ.copy(),
            # An environment variable to indicate that the dbt CLI is being invoked from Dagster.
            "DAGSTER_DBT_CLI": "true",
            # Run dbt with unbuffered output.
            "PYTHONUNBUFFERED": "1",
            # Disable anonymous usage statistics for performance.
            "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
            # The DBT_LOG_FORMAT environment variable must be set to `json`. We use this
            # environment variable to ensure that the dbt CLI outputs structured logs.
            "DBT_LOG_FORMAT": "json",
            # The DBT_TARGET_PATH environment variable is set to a unique value for each dbt
            # invocation so that artifact paths are separated.
            # See https://discourse.getdbt.com/t/multiple-run-results-json-and-manifest-json-files/7555
            # for more information.
            "DBT_TARGET_PATH": os.fspath(target_path),
            # The DBT_LOG_PATH environment variable is set to the same value as DBT_TARGET_PATH
            # so that logs for each dbt invocation has separate log files.
            "DBT_LOG_PATH": os.fspath(target_path),
            # The DBT_PROFILES_DIR environment variable is set to the path containing the dbt
            # profiles.yml file.
            # See https://docs.getdbt.com/docs/core/connect-data-platform/connection-profiles#advanced-customizing-a-profile-directory
            # for more information.
            **({"DBT_PROFILES_DIR": self.profiles_dir} if self.profiles_dir else {}),
            # The DBT_PROJECT_DIR environment variable is set to the path containing the dbt project
            # See https://docs.getdbt.com/reference/dbt_project.yml for more information.
            "DBT_PROJECT_DIR": str(project_dir),
        }

        # set dbt indirect selection if needed to execute specific dbt tests due to asset check
        # selection
        if indirect_selection:
            env[DBT_INDIRECT_SELECTION_ENV] = indirect_selection

        # TODO: verify that args does not have any selection flags if the context and manifest
        # are passed to this function.
        profile_args: list[str] = []
        if self.profile:
            profile_args = ["--profile", self.profile]

        if self.target:
            profile_args += ["--target", self.target]

        full_dbt_args = [
            self.dbt_executable,
            *self.global_config_flags,
            *args,
            *profile_args,
            *selection_args,
        ]

        if not target_path.is_absolute():
            target_path = project_dir.joinpath(target_path)

        # run dbt --version to get the dbt core version
        adapter: Optional[BaseAdapter] = None
        with pushd(str(project_dir)):
            # we do not need to initialize the adapter if we are using the fusion engine
            if self._cli_version.major < 2:
                try:
                    adapter = self._initialize_dbt_core_adapter(args)
                except:
                    logger.warning(
                        "An error was encountered when creating a handle to the dbt adapter in Dagster.",
                        exc_info=True,
                    )

            return DbtCliInvocation.run(
                args=full_dbt_args,
                env=env,
                manifest=manifest,
                dagster_dbt_translator=dagster_dbt_translator,
                project_dir=project_dir,
                target_path=target_path,
                raise_on_error=raise_on_error,
                context=context,
                adapter=adapter,
                cli_version=self._cli_version,
                dbt_project=updated_params.dbt_project,
            )

    def setup_for_execution(self, context: InitResourceContext) -> None:
        packages_yaml = Path(self.project_dir).joinpath("packages.yml")
        dependencies_yaml = Path(self.project_dir).joinpath("dependencies.yml")

        if context.log and (
            (packages_yaml.exists() and _dbt_packages_has_dagster_dbt(packages_yaml))
            or (dependencies_yaml.exists() and _dbt_packages_has_dagster_dbt(dependencies_yaml))
        ):
            context.log.warn(
                "Fetching column metadata using `log_column_level_metadata` macro is deprecated and will be"
                " removed in dagster-dbt 0.24.0. Use the `fetch_column_metadata` method in your asset definition"
                " to fetch column metadata instead."
            )
