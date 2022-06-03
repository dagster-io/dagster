from typing import Any, Dict, List, Optional, Set

import dagster._check as check
from dagster import Permissive, resource
from dagster.utils.merger import merge_dicts

from ..dbt_resource import DbtResource
from .constants import CLI_COMMON_FLAGS_CONFIG_SCHEMA, CLI_COMMON_OPTIONS_CONFIG_SCHEMA
from .types import DbtCliOutput
from .utils import execute_cli, parse_manifest, parse_run_results


class DbtCliResource(DbtResource):
    """
    A resource that allows you to execute dbt cli commands. For the most up-to-date documentation on
    the specific parameters available to you for each command, check out the dbt docs:

    https://docs.getdbt.com/reference/commands/run

    To use this as a dagster resource, we recommend using
    :func:`dbt_cli_resource <dagster_dbt.dbt_cli_resource>`.
    """

    def __init__(
        self,
        executable: str,
        default_flags: Dict[str, Any],
        warn_error: bool,
        ignore_handled_error: bool,
        target_path: str,
        logger: Optional[Any] = None,
        docs_url: Optional[str] = None,
    ):
        self._default_flags = default_flags
        self._executable = executable
        self._warn_error = warn_error
        self._ignore_handled_error = ignore_handled_error
        self._target_path = target_path
        self._docs_url = docs_url
        super().__init__(logger)

    @property
    def default_flags(self) -> Dict[str, Any]:
        """
        A set of params populated from resource config that are passed as flags to each dbt CLI command.
        """
        return self._format_params(self._default_flags, replace_underscores=True)

    @property
    def strict_flags(self) -> Set[str]:
        """
        A set of flags that should not be auto-populated from the default flags unless they are
            arguments to the associated function.
        """
        return {"models", "exclude", "select"}

    def cli(self, command: str, **kwargs) -> DbtCliOutput:
        """
        Executes a dbt CLI command. Params passed in as keyword arguments will be merged with the
            default flags that were configured on resource initialization (if any) overriding the
            default values if necessary.

        Args:
            command (str): The command you wish to run (e.g. 'run', 'test', 'docs generate', etc.)

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        command = check.str_param(command, "command")
        extra_flags = {} if kwargs is None else kwargs

        # remove default flags that are declared as "strict" and not explicitly passed in
        default_flags = {
            k: v
            for k, v in self.default_flags.items()
            if not (k in self.strict_flags and k not in extra_flags)
        }

        flags = merge_dicts(
            default_flags, self._format_params(extra_flags, replace_underscores=True)
        )

        return execute_cli(
            executable=self._executable,
            command=command,
            flags_dict=flags,
            log=self.logger,
            warn_error=self._warn_error,
            ignore_handled_error=self._ignore_handled_error,
            target_path=self._target_path,
            docs_url=self._docs_url,
        )

    def compile(
        self, models: Optional[List[str]] = None, exclude: Optional[List[str]] = None, **kwargs
    ) -> DbtCliOutput:
        """
        Run the ``compile`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            models (List[str], optional): the models to include in compilation.
            exclude (List[str]), optional): the models to exclude from compilation.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("compile", models=models, exclude=exclude, **kwargs)

    def run(
        self, models: Optional[List[str]] = None, exclude: Optional[List[str]] = None, **kwargs
    ) -> DbtCliOutput:
        """
        Run the ``run`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            models (List[str], optional): the models to include in compilation.
            exclude (List[str]), optional): the models to exclude from compilation.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("run", models=models, exclude=exclude, **kwargs)

    def snapshot(
        self, select: Optional[List[str]] = None, exclude: Optional[List[str]] = None, **kwargs
    ) -> DbtCliOutput:
        """
        Run the ``snapshot`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            select (List[str], optional): the snapshots to include in the run.
            exclude (List[str], optional): the snapshots to exclude from the run.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("snapshot", select=select, exclude=exclude, **kwargs)

    def test(
        self,
        models: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        data: bool = True,
        schema: bool = True,
        **kwargs,
    ) -> DbtCliOutput:
        """
        Run the ``test`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            models (List[str], optional): the models to include in testing.
            exclude (List[str], optional): the models to exclude from testing.
            data (bool, optional): If ``True`` (default), then run data tests.
            schema (bool, optional): If ``True`` (default), then run schema tests.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        if data and schema:
            # do not include these arguments if both are True, as these are deprecated in later
            # versions of dbt, and for older versions the functionality is the same regardless of
            # if both are set or neither are set.
            return self.cli("test", models=models, exclude=exclude, **kwargs)
        return self.cli("test", models=models, exclude=exclude, data=data, schema=schema, **kwargs)

    def seed(
        self,
        show: bool = False,
        select: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        **kwargs,
    ) -> DbtCliOutput:
        """
        Run the ``seed`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            show (bool, optional): If ``True``, then show a sample of the seeded data in the
                response. Defaults to ``False``.
            select (List[str], optional): the snapshots to include in the run.
            exclude (List[str], optional): the snapshots to exclude from the run.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("seed", show=show, select=select, exclude=exclude, **kwargs)

    def ls(
        self,
        select: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        **kwargs,
    ) -> DbtCliOutput:
        """
        Run the ``ls`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            select (List[str], optional): the resources to include in the output.
            models (List[str], optional): the models to include in the output.
            exclude (List[str], optional): the resources to exclude from the output.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("ls", select=select, models=models, exclude=exclude, **kwargs)

    def build(self, select: Optional[List[str]] = None, **kwargs) -> DbtCliOutput:
        """
        Run the ``build`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            select (List[str], optional): the models/resources to include in the run.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("build", select=select, **kwargs)

    def freshness(self, select: Optional[List[str]] = None, **kwargs) -> DbtCliOutput:
        """
        Run the ``source snapshot-freshness`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            select (List[str], optional): the sources to include in the run.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("source snapshot-freshness", select=select, **kwargs)

    def generate_docs(self, compile_project: bool = False, **kwargs) -> DbtCliOutput:
        """
        Run the ``docs generate`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            compile_project (bool, optional): If true, compile the project before generating a catalog.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """
        return self.cli("docs generate", compile=compile_project, **kwargs)

    def run_operation(
        self, macro: str, args: Optional[Dict[str, Any]] = None, **kwargs
    ) -> DbtCliOutput:
        """
        Run the ``run-operation`` command on a dbt project. kwargs are passed in as additional parameters.

        Args:
            macro (str): the dbt macro to invoke.
            args (Dict[str, Any], optional): the keyword arguments to be supplied to the macro.

        Returns:
            DbtCliOutput: An instance of :class:`DbtCliOutput<dagster_dbt.DbtCliOutput>` containing
                parsed log output as well as the contents of run_results.json (if applicable).
        """

        return self.cli(f"run-operation {macro}", args=args, **kwargs)

    def get_run_results_json(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get a parsed version of the run_results.json file for the relevant dbt project.

        Returns:
            Dict[str, Any]: dictionary containing the parsed contents of the manifest json file
                for this dbt project.
        """
        project_dir = kwargs.get("project_dir", self.default_flags["project-dir"])
        target_path = kwargs.get("target_path", self._target_path)
        return parse_run_results(project_dir, target_path)

    def get_manifest_json(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Get a parsed version of the manifest.json file for the relevant dbt project.

        Returns:
            Dict[str, Any]: dictionary containing the parsed contents of the manifest json file
                for this dbt project.
        """
        project_dir = kwargs.get("project_dir", self.default_flags["project-dir"])
        target_path = kwargs.get("target_path", self._target_path)
        return parse_manifest(project_dir, target_path)


@resource(
    config_schema=Permissive(
        {
            k.replace("-", "_"): v
            for k, v in dict(
                **CLI_COMMON_FLAGS_CONFIG_SCHEMA, **CLI_COMMON_OPTIONS_CONFIG_SCHEMA
            ).items()
        }
    ),
    description="A resource that can run dbt CLI commands.",
)
def dbt_cli_resource(context) -> DbtCliResource:
    """This resource defines a dbt CLI interface.

    To configure this resource, we recommend using the `configured
    <https://docs.dagster.io/concepts/configuration/configured>`_ method.

    Examples:

    .. code-block:: python

        custom_dbt_cli_resource = dbt_cli_resource.configured({"project-dir": "path/to/my/dbt_project"})

        @pipeline(mode_defs=[ModeDefinition(resource_defs={"dbt": custom_dbt_cli_resource})])
        def dbt_cli_pipeline():
            # Run solids with `required_resource_keys={"dbt", ...}`.

    You may configure this resource as follows:

    .. code-block:: YAML

        resources:
          dbt_cli_resource:
            config:
              project_dir: "."
              # Optional[str]: Which directory to look in for the dbt_project.yml file. Default is
              # the current working directory and its parents.
              profiles_dir: $DBT_PROFILES_DIR or $HOME/.dbt
              # Optional[str]: Which directory to look in for the profiles.yml file.
              profile: ""
              # Optional[str]: Which profile to load. Overrides setting in dbt_project.yml.
              target: ""
              # Optional[str]: Which target to load for the given profile.
              vars: {}
              # Optional[Permissive]: Supply variables to the project. This argument overrides
              # variables defined in your dbt_project.yml file. This argument should be a
              # dictionary, eg. "{'my_variable': 'my_value'}"
              bypass_cache: False
              # Optional[bool]: If set, bypass the adapter-level cache of database state.


    """
    # set of options in the config schema that are not flags
    non_flag_options = {k.replace("-", "_") for k in CLI_COMMON_OPTIONS_CONFIG_SCHEMA}
    # all config options that are intended to be used as flags for dbt commands
    default_flags = {k: v for k, v in context.resource_config.items() if k not in non_flag_options}
    return DbtCliResource(
        executable=context.resource_config["dbt_executable"],
        default_flags=default_flags,
        warn_error=context.resource_config["warn_error"],
        ignore_handled_error=context.resource_config["ignore_handled_error"],
        target_path=context.resource_config["target_path"],
        logger=context.log,
        docs_url=context.resource_config.get("docs_url"),
    )
