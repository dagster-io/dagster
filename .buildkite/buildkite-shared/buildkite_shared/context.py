import logging
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Generic, Literal, TypeAlias, overload

from buildkite_shared.python_packages import PythonPackagesData
from buildkite_shared.step_builders.step_builder import StepConfiguration
from buildkite_shared.transform import filter_steps, repeat_steps, simplify_steps
from buildkite_shared.utils import pushd
from packaging import version
from typing_extensions import Self, TypeVar

INTERNAL_OSS_PREFIX = "dagster-oss"

T_Config = TypeVar("T_Config", bound="BuildConfig", default="BuildConfig", covariant=True)


class BuildkiteContext(Generic[T_Config]):
    def __init__(
        self,
        repo_path: Path,
        env: Mapping[str, str],
        config: T_Config,
        changed_files: frozenset[Path],
        python_packages: PythonPackagesData,
    ) -> None:
        self.repo_path = repo_path
        self.env = env
        self.config = config
        self.changed_files = changed_files
        self.python_packages = python_packages

    @classmethod
    def create(cls, env: Mapping[str, str] = os.environ) -> Self:
        repo_path = Path.cwd()
        message = _get_required_env_var("BUILDKITE_MESSAGE", env)
        config = cls.extract_build_config(message)

        changed_files = _discover_changed_files(repo_path)
        python_packages = PythonPackagesData.load(repo_path, changed_files)
        return cls(
            repo_path=repo_path,
            env=env,
            config=config,
            changed_files=changed_files,
            python_packages=python_packages,
        )

    @classmethod
    def extract_build_config(cls, message: str) -> "BuildConfig":
        return BuildConfig.from_message(message)

    @overload
    def get_env(self, var: "BuildkiteEnvVar") -> str | None: ...

    @overload
    def get_env(self, var: "BuildkiteEnvVar", default: None) -> str | None: ...

    @overload
    def get_env(self, var: "BuildkiteEnvVar", default: str) -> str: ...

    def get_env(self, var: "BuildkiteEnvVar", default: str | None = None):
        return self.env.get(var, default)

    def getx_env(self, var: "BuildkiteEnvVar") -> str:
        return _get_required_env_var(var, self.env)

    @property
    def branch(self) -> str:
        return self.getx_env("BUILDKITE_BRANCH")

    @property
    def message(self) -> str:
        return self.getx_env("BUILDKITE_MESSAGE")

    @cached_property
    def commit_hash(self) -> str:
        env_commit = self.getx_env("BUILDKITE_COMMIT")
        return (
            env_commit
            if len(env_commit) != 40
            # not a full commit hash, likely a symbolic ref like HEAD
            else subprocess.check_output(["git", "rev-parse", env_commit]).decode().strip()
        )

    @property
    def is_release_branch(self) -> bool:
        return _is_release_branch(self.branch)

    @property
    def is_master_branch(self) -> bool:
        return _is_master_branch(self.branch)

    @property
    def is_feature_branch(self) -> bool:
        return _is_feature_branch(self.branch)

    @property
    def pipeline_slug(self) -> str:
        return self.getx_env("BUILDKITE_PIPELINE_SLUG")

    def is_triggered_job(self) -> bool:
        # Builds triggered by another Buildkite build have a source of "trigger_job"
        # Builds triggered by commits to a Github repo have a source of "webhook"
        return self.get_env("BUILDKITE_SOURCE") == "trigger_job"

    @property
    def release_version(self) -> version.Version:
        self.require_release_branch()
        return version.parse(self.branch.split("-")[-1])

    def require_release_branch(self) -> None:
        if not self.is_release_branch:
            raise ValueError(f"Branch {self.branch} is not a release branch")

    @cached_property
    def all_changed_oss_files(self) -> frozenset[Path]:
        if (self.repo_path / INTERNAL_OSS_PREFIX).exists():  # is internal
            return frozenset(
                {
                    _strip_oss_prefix(path)
                    for path in self.changed_files
                    if path.parts[0] == INTERNAL_OSS_PREFIX
                }
            )
        else:
            return self.changed_files

    def apply_transforms(self, steps: Sequence[StepConfiguration]) -> Sequence[StepConfiguration]:
        # Filter and repeat settings are only applied on feature branches.
        if self.is_feature_branch and self.config.step_filter:
            steps = filter_steps(
                steps, lambda step: self.config.step_filter in step.get("label", "")
            )
        if self.is_feature_branch and self.config.repeat > 1:
            steps = repeat_steps(steps, self.config.repeat)
        return simplify_steps(steps)


@dataclass
class BuildConfig:
    # Forces all steps to run, even if they would normally be skipped by the step filter.
    no_skip: bool
    # A substring that will be used to filter the steps to run. The filter
    # predicate is `substring in step["label"]`.
    step_filter: str | None
    # An integer specifying how many times to run each step. Primarily useful
    # when combined with the STEP_FILTER directive to run a subset of steps
    # multiple times, for example to surface flaky tests.
    repeat: int

    @classmethod
    def from_raw(cls, raw: Mapping[str, str]) -> Self:
        return cls(
            no_skip=bool(raw.get("no_skip")),
            step_filter=raw.get("step_filter"),
            repeat=int(raw.get("repeat", "1")),
        )

    @classmethod
    def from_message(cls, buildkite_message: str) -> Self:
        """Parses build params from the build message (usually the commit message).

        Build params are set via "magic strings" that can be put anywhere in the message.

        Note that build params are not a buildkite concept. They are a convention
        we use to allow developers to easily control builds.

        The format for build params is [VAR=VALUE], where VAR is the name of the
        build parameter and VALUE is the value to set it to. Value can also be
        omitted, which is equivalent to setting to "TRUE".

        VAR and VALUE must contain only letters, numbers, and underscores.

        For example, a commit message of "Fix bug [STEP_FILTER=integration]
        [REPEAT=5]" would set the TEST_ONLY and TEST_ONLY_N_TIMES
        directives for the build.
        """
        field_names = {field.name for field in cls.__dataclass_fields__.values()}
        pattern = r"\[([A-Za-z0-9_]+)(?:=([A-Za-z0-9_]+))?\]"
        matches: list[tuple[str, str]] = re.findall(pattern, buildkite_message)
        params: dict[str, str] = {}
        for var, value in matches:
            var_norm = var.lower()
            if var_norm not in field_names:
                logging.warning(f"Ignoring unrecognized param in message: {var}")
                continue
            norm_value = value or "TRUE"
            logging.info(f"Extracted param from message: {var}={norm_value}")
            params[var] = norm_value
        return cls.from_raw(params)


## Buildkite environment variables.
BuildkiteEnvVar: TypeAlias = Literal[
    # Always true
    "BUILDKITE",
    # The value of the debug agent configuration option.
    "BUILDKITE_AGENT_DEBUG",
    # The value of the disconnect-after-job agent configuration option.
    "BUILDKITE_AGENT_DISCONNECT_AFTER_JOB",
    # The value of the disconnect-after-idle-timeout agent configuration option.
    "BUILDKITE_AGENT_DISCONNECT_AFTER_IDLE_TIMEOUT",
    # The value of the endpoint agent configuration option. This is set as an environment variable by the bootstrap and then read by most of the buildkite-agent commands.
    "BUILDKITE_AGENT_ENDPOINT",
    # A list of the experimental agent features that are currently enabled. The value can be set using the --experiment flag on the buildkite-agent start command or in your agent configuration file.
    "BUILDKITE_AGENT_EXPERIMENT",
    # The value of the health-check-addr agent configuration option.
    "BUILDKITE_AGENT_HEALTH_CHECK_ADDR",
    # The UUID of the agent.
    "BUILDKITE_AGENT_ID",
    # The value of each agent tag. The tag name is appended to the end of the variable name. They can be set using the --tags flag on the buildkite-agent start command, or in the agent configuration file. The Queue tag is specifically used for isolating jobs and agents, and appears as the BUILDKITE_AGENT_META_DATA_QUEUE environment variable.
    "BUILDKITE_AGENT_META_DATA_",
    # The name of the agent that ran the job.
    "BUILDKITE_AGENT_NAME",
    # The process ID of the agent.
    "BUILDKITE_AGENT_PID",
    # The artifact paths to upload after the job, if any have been specified. The value can be modified by exporting the environment variable in the environment or pre-checkout hooks.
    "BUILDKITE_ARTIFACT_PATHS",
    # The path where artifacts will be uploaded. This variable is read by the buildkite-agent artifact upload command, and during the artifact upload phase of command steps. It can only be set by exporting the environment variable in the environment, pre-checkout or pre-command hooks.
    "BUILDKITE_ARTIFACT_UPLOAD_DESTINATION",
    # The path to the directory containing the buildkite-agent binary.
    "BUILDKITE_BIN_PATH",
    # The branch being built. Note that for manually triggered builds, this branch is not guaranteed to contain the commit specified by BUILDKITE_COMMIT.
    "BUILDKITE_BRANCH",
    # The path where the agent has checked out your code for this build. This variable is read by the bootstrap when the agent is started, and can only be set by exporting the environment variable in the environment or pre-checkout hooks.
    "BUILDKITE_BUILD_CHECKOUT_PATH",
    # The name of the user who authored the commit being built. May be unverified. This value can be blank in some situations, including builds manually triggered using API or Buildkite web interface.
    "BUILDKITE_BUILD_AUTHOR",
    # The notification email of the user who authored the commit being built. May be unverified. This value can be blank in some situations, including builds manually triggered using API or Buildkite web interface.
    "BUILDKITE_BUILD_AUTHOR_EMAIL",
    # The name of the user who created the build.
    "BUILDKITE_BUILD_CREATOR",
    # The notification email of the user who created the build.
    "BUILDKITE_BUILD_CREATOR_EMAIL",
    # A colon separated list of non-private team slugs that the build creator belongs to.
    "BUILDKITE_BUILD_CREATOR_TEAMS",
    # The UUID of the build.
    "BUILDKITE_BUILD_ID",
    # The build number. This number increases with every build, and is guaranteed to be unique within each pipeline.
    "BUILDKITE_BUILD_NUMBER",
    # The value of the build-path agent configuration option.
    "BUILDKITE_BUILD_PATH",
    # The url for this build on Buildkite.
    "BUILDKITE_BUILD_URL",
    # The value of the cancel-grace-period agent configuration option in seconds.
    "BUILDKITE_CANCEL_GRACE_PERIOD",
    # The value of the cancel-signal agent configuration option. The value can be modified by exporting the environment variable in the environment or pre-checkout hooks.
    "BUILDKITE_CANCEL_SIGNAL",
    # Whether the build should perform a clean checkout. The variable is read during the default checkout phase of the bootstrap and can be overridden in environment or pre-checkout hooks.
    "BUILDKITE_CLEAN_CHECKOUT",
    # The UUID value of the cluster, but only if the build has an associated cluster_queue. Otherwise, this environment variable is not set.
    "BUILDKITE_CLUSTER_ID",
    # The name of the cluster in which the job is running.
    "BUILDKITE_CLUSTER_NAME",
    # The command that will be run for the job.
    "BUILDKITE_COMMAND",
    # The opposite of the value of the no-command-eval agent configuration option.
    "BUILDKITE_COMMAND_EVAL",
    # The exit code from the last command run in the command hook.
    "BUILDKITE_COMMAND_EXIT_STATUS",
    # hosted if the job is running on Hosted Agents, otherwise self-hosted.
    "BUILDKITE_COMPUTE_TYPE",
    # The git commit object of the build. This is usually a 40-byte hexadecimal SHA-1 hash, but can also be a symbolic name like HEAD.
    "BUILDKITE_COMMIT",
    # The path to the agent config file.
    "BUILDKITE_CONFIG_PATH",
    # The path to the file containing the job's environment variables.
    "BUILDKITE_ENV_FILE",
    # The value of the git-clean-flags agent configuration option. The value can be modified by exporting the environment variable in the environment or pre-checkout hooks.
    "BUILDKITE_GIT_CLEAN_FLAGS",
    # The value of the git-clone-flags agent configuration option. The value can be modified by exporting the environment variable in the environment or pre-checkout hooks.
    "BUILDKITE_GIT_CLONE_FLAGS",
    # The UUID of the group step the job belongs to. This variable is only available if the job belongs to a group step.
    "BUILDKITE_GROUP_ID",
    # The value of the key attribute of the group step the job belongs to. This variable is only available if the job belongs to a group step.
    "BUILDKITE_GROUP_KEY",
    # The label/name of the group step the job belongs to. This variable is only available if the job belongs to a group step.
    "BUILDKITE_GROUP_LABEL",
    # The value of the hooks-path agent configuration option.
    "BUILDKITE_HOOKS_PATH",
    # A list of environment variables that have been set in your pipeline that are protected and will be overridden, used internally to pass data from the bootstrap to the agent.
    "BUILDKITE_IGNORED_ENV",
    # The internal UUID Buildkite uses for this job.
    "BUILDKITE_JOB_ID",
    # Is initially undefined, but gets defined with the value true by the agent when the job has been canceled. This value can be used by subsequent hooks to opt out of executing.
    "BUILDKITE_JOB_CANCELLED",
    # The path to a temporary file containing the logs for this job. Requires enabling the enable-job-log-tmpfile agent configuration option.
    "BUILDKITE_JOB_LOG_TMPFILE",
    # The label/name of the current job.
    "BUILDKITE_LABEL",
    # The exit code of the last hook that ran, used internally by the hooks.
    "BUILDKITE_LAST_HOOK_EXIT_STATUS",
    # The opposite of the value of the no-local-hooks agent configuration option.
    "BUILDKITE_LOCAL_HOOKS_ENABLED",
    # The message associated with the build, usually the commit message or the message provided when the build is triggered.
    "BUILDKITE_MESSAGE",
    # The UUID of the organization.
    "BUILDKITE_ORGANIZATION_ID",
    # The organization name on Buildkite as used in URLs.
    "BUILDKITE_ORGANIZATION_SLUG",
    # The index of each parallel job created from a parallel build step, starting from 0.
    "BUILDKITE_PARALLEL_JOB",
    # The total number of parallel jobs created from a parallel build step.
    "BUILDKITE_PARALLEL_JOB_COUNT",
    # The default branch for this pipeline.
    "BUILDKITE_PIPELINE_DEFAULT_BRANCH",
    # The UUID of the pipeline.
    "BUILDKITE_PIPELINE_ID",
    # The displayed pipeline name on Buildkite.
    "BUILDKITE_PIPELINE_NAME",
    # The ID of the source code provider for the pipeline's repository.
    "BUILDKITE_PIPELINE_PROVIDER",
    # The pipeline slug on Buildkite as used in URLs.
    "BUILDKITE_PIPELINE_SLUG",
    # The slug of the step suite.
    "BUILDKITE_STEP_SUITE_SLUG",
    # A colon separated list of the pipeline's non-private team slugs.
    "BUILDKITE_PIPELINE_TEAMS",
    # A JSON string holding the current plugin's configuration (as opposed to all the plugin configurations in the BUILDKITE_PLUGINS environment variable).
    "BUILDKITE_PLUGIN_CONFIGURATION",
    # The current plugin's name, with all letters in uppercase and any spaces replaced with underscores.
    "BUILDKITE_PLUGIN_NAME",
    # A JSON object containing a list plugins used in the step, and their configuration.
    "BUILDKITE_PLUGINS",
    # The opposite of the value of the no-plugins agent configuration option.
    "BUILDKITE_PLUGINS_ENABLED",
    # The value of the plugins-path agent configuration option.
    "BUILDKITE_PLUGINS_PATH",
    # Whether to validate plugin configuration and requirements.
    "BUILDKITE_PLUGIN_VALIDATION",
    # The number of the pull request or false if not a pull request.
    "BUILDKITE_PULL_REQUEST",
    # The base branch that the pull request is targeting or "" if not a pull request.
    "BUILDKITE_PULL_REQUEST_BASE_BRANCH",
    # Set to true when the pull request is a draft. This variable is only available if a build contains a draft pull request.
    "BUILDKITE_PULL_REQUEST_DRAFT",
    # The repository URL of the pull request or "" if not a pull request.
    "BUILDKITE_PULL_REQUEST_REPO",
    # The UUID of the original build this was rebuilt from or "" if not a rebuild.
    "BUILDKITE_REBUILT_FROM_BUILD_ID",
    # The number of the original build this was rebuilt from or "" if not a rebuild.
    "BUILDKITE_REBUILT_FROM_BUILD_NUMBER",
    # A custom refspec for the buildkite-agent bootstrap script to use when checking out code.
    "BUILDKITE_REFSPEC",
    # The repository of your pipeline. This variable can be set by exporting the environment variable in the environment or pre-checkout hooks.
    "BUILDKITE_REPO",
    # The path to the shared git mirror. Introduced in v3.47.0.
    "BUILDKITE_REPO_MIRROR",
    # How many times this job has been retried.
    "BUILDKITE_RETRY_COUNT",
    # The value of the shell agent configuration option.
    "BUILDKITE_SHELL",
    # The source of the event that created the build.
    "BUILDKITE_SOURCE",
    # The opposite of the value of the no-ssh-keyscan agent configuration option.
    "BUILDKITE_SSH_KEYSCAN",
    # A unique string that identifies a step.
    "BUILDKITE_STEP_ID",
    # The value of the key command step attribute, a unique string set by you to identify a step.
    "BUILDKITE_STEP_KEY",
    # The name of the tag being built, if this build was triggered from a tag.
    "BUILDKITE_TAG",
    # The token used to access the Buildkite API for quarantined tests or steps
    "BUILDKITE_TEST_QUARANTINE_TOKEN",
    # The number of minutes until Buildkite automatically cancels this job, if a timeout has been specified, otherwise it false if no timeout is set.
    "BUILDKITE_TIMEOUT",
    # Set to "datadog" to send metrics to the Datadog APM using localhost:8126, or DD_AGENT_HOST:DD_AGENT_APM_PORT.
    "BUILDKITE_TRACING_BACKEND",
    # The UUID of the build that triggered this build. This will be empty if the build was not triggered from another build.
    "BUILDKITE_TRIGGERED_FROM_BUILD_ID",
    # The number of the build that triggered this build or "" if the build was not triggered from another build.
    "BUILDKITE_TRIGGERED_FROM_BUILD_NUMBER",
    # The slug of the pipeline that was used to trigger this build or "" if the build was not triggered from another build.
    "BUILDKITE_TRIGGERED_FROM_BUILD_PIPELINE_SLUG",
    # The name of the user who unblocked the build.
    "BUILDKITE_UNBLOCKER",
    # The notification email of the user who unblocked the build.
    "BUILDKITE_UNBLOCKER_EMAIL",
    # The UUID of the user who unblocked the build.
    "BUILDKITE_UNBLOCKER_ID",
    # A colon separated list of non-private team slugs that the user who unblocked the build belongs to.
    "BUILDKITE_UNBLOCKER_TEAMS",
    # Always true in a Buildkite job
    "CI",
]


def _get_required_env_var(var: str, env: Mapping[str, str]) -> str:
    if var not in env:
        raise Exception(f"Missing required environment variable: {var}")
    return env[var]


def _is_release_branch(branch: str) -> bool:
    return branch.startswith("release-")


def _is_master_branch(branch: str) -> bool:
    return branch == "master"


def _is_feature_branch(branch: str) -> bool:
    return not _is_release_branch(branch) and not _is_master_branch(branch)


def _strip_oss_prefix(path: Path) -> Path:
    """If the path is within the dagster-oss/ directory, strip that prefix."""
    return Path(*path.parts[1:]) if next(iter(path.parts), None) == INTERNAL_OSS_PREFIX else path


def _discover_changed_files(repo_path: Path) -> frozenset[Path]:
    """Shared logic for loading changed files from git. Returns (all_files, all_oss_files)."""
    # Mark current directory as safe (needed when running from internal repo's dagster-oss/)
    with pushd(repo_path):
        subprocess.call(["git", "config", "--global", "--add", "safe.directory", os.getcwd()])

        subprocess.call(["git", "fetch", "origin", "master"])
        origin = _get_commit("origin/master")
        head = _get_commit("HEAD")
        logging.info(f"Changed files between origin/master ({origin}) and HEAD ({head}):")
        paths = (
            subprocess.check_output(
                [
                    "git",
                    "diff",
                    "origin/master...HEAD",
                    "--name-only",
                    "--relative",  # Paths relative to cwd
                    "--",
                    ".",  # Only files in current directory
                ]
            )
            .decode("utf-8")
            .strip()
            .split("\n")
        )

        all_files: set[Path] = set()
        for path in sorted(paths):
            if path:
                logging.info("  - " + path)
                all_files.add(Path(path))

    return frozenset(all_files)


def _get_commit(rev):
    return subprocess.check_output(["git", "rev-parse", "--short", rev]).decode("utf-8").strip()
