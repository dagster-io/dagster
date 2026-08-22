import os
import re
import shutil
import subprocess
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Annotated
from urllib.parse import quote, urlparse, urlunparse

import dagster._check as check
from dagster._core.errors import DagsterInvalidDefinitionError
from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Resolver

from dagster_dbt.dbt_project import DbtProject

if TYPE_CHECKING:
    from dagster_dbt.components.dbt_project.component import DbtProjectArgs

# GitPython imposed no clone timeout, so the default here has to be generous enough that a large
# shallow clone on a slow link does not start failing on upgrade. Overridable for the rest.
_GIT_CLONE_TIMEOUT_SECONDS = int(os.getenv("DAGSTER_DBT_GIT_CLONE_TIMEOUT_SECONDS", "1800"))
_URL_USERINFO = re.compile(r"(https?://)[^/\s'\"@]+@")


def _redact_userinfo(text: str) -> str:
    """Strip URL userinfo so clone tokens are not interpolated into errors."""
    return _URL_USERINFO.sub(r"\1", text)


def _shallow_clone(repo_url: str, dest: Path, *, display_url: str | None = None) -> None:
    """Shallow-clone ``repo_url`` into ``dest`` using the git CLI."""
    repo_url = check.str_param(repo_url, "repo_url")
    dest = check.inst_param(dest, "dest", Path)
    label = _redact_userinfo(display_url if display_url is not None else repo_url)
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
    try:
        completed = subprocess.run(
            ["git", "clone", "--depth", "1", "--", repo_url, str(dest)],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=_GIT_CLONE_TIMEOUT_SECONDS,
            env=env,
        )
    except FileNotFoundError as err:
        raise DagsterInvalidDefinitionError(
            "git executable not found on PATH. Install git to clone remote dbt projects."
        ) from err
    except subprocess.TimeoutExpired:
        # Do not chain TimeoutExpired: its argv includes the clone URL with credentials.
        raise DagsterInvalidDefinitionError(
            f"Timed out cloning git repository {label} into {dest}."
        ) from None
    if completed.returncode != 0:
        raise DagsterInvalidDefinitionError(
            f"Failed to clone git repository {label} into {dest}. "
            f"git exited with code {completed.returncode}: {_redact_userinfo(completed.stderr)}"
        )


def _ignore_nested_dest(dest: Path):
    """Returns an ``ignore`` callable for ``shutil.copytree`` that prevents the copy from
    descending into its own destination directory when ``dest`` is nested inside the source
    tree. This guards against unbounded recursive copying that would otherwise fill the disk.
    """
    resolved_dest = dest.resolve()

    def _ignore(src_dir: str, names: list[str]) -> set[str]:
        src_path = Path(src_dir).resolve()
        return {name for name in names if (src_path / name).resolve() == resolved_dest}

    return _ignore


class DbtProjectManager(ABC):
    """Helper class that wraps a dbt project that may or may not be available on local disk at the time
    it is instantiated. Provides methods for syncing the project to a local path and for instantiating the
    final DbtProject object when ready.
    """

    @property
    @abstractmethod
    def defs_state_discriminator(self) -> str: ...

    @abstractmethod
    def sync(self, state_path: Path) -> None: ...

    def _local_project_dir(self, state_path: Path) -> Path:
        return state_path.parent / "project"

    def prepare(self, state_path: Path) -> None:
        """Syncs the project to the given local path and ensures the manifest is generated
        and the dependencies are installed.
        """
        # ensure local dir is empty
        local_dir = self._local_project_dir(state_path)
        if local_dir.exists():
            shutil.rmtree(local_dir)
        local_dir.mkdir(parents=True, exist_ok=True)

        # ensure project exists in the dir and is compiled
        self.sync(state_path)

        # indicate that project has been prepared
        state_path.touch()

    @abstractmethod
    def get_project(self, state_path: Path | None) -> "DbtProject": ...


@dataclass
class NoopDbtProjectManager(DbtProjectManager):
    """Wraps a DbtProject that has already been fully instantiated. Used for cases where a
    user directly provides a DbtProject to the DbtProjectComponent.
    """

    project: "DbtProject"

    @property
    def defs_state_discriminator(self) -> str:
        return self.project.name

    def sync(self, state_path: Path) -> None:
        pass

    def get_project(self, state_path: Path | None) -> DbtProject:
        return self.project


@dataclass
class DbtProjectArgsManager(DbtProjectManager):
    """Wraps DbtProjectArgs provided to the DbtProjectComponent. Avoids instantiating the DbtProject object
    immediately as this would cause errors in cases where the project_dir has not yet been synced.
    """

    args: "DbtProjectArgs"

    @property
    def defs_state_discriminator(self) -> str:
        return Path(self.args.project_dir).stem

    def sync(self, state_path: Path) -> None:
        # we prepare the project in the original project directory rather than the new one
        # so that code that does not have access to the local state path can still access
        # the manifest.json file.
        project = self.get_project(None)
        project.preparer.prepare(project)
        dest = self._local_project_dir(state_path)
        # When the dbt project lives at (or above) the local state directory -- e.g. when the
        # dbt project is at the root of the Dagster project -- `dest` is nested inside the source
        # directory. Without ignoring it, copytree recurses into its own destination and copies
        # the project into itself unboundedly, filling up the disk.
        shutil.copytree(
            self.args.project_dir, dest, dirs_exist_ok=True, ignore=_ignore_nested_dest(dest)
        )

    def get_project(self, state_path: Path | None) -> "DbtProject":
        kwargs = asdict(self.args)

        project_dir = self._local_project_dir(state_path) if state_path else self.args.project_dir
        return DbtProject(
            project_dir=project_dir,
            # allow default values on DbtProject to take precedence
            **{k: v for k, v in kwargs.items() if v is not None and k != "project_dir"},
        )


@dataclass
class RemoteGitDbtProjectManager(DbtProjectManager, Resolvable):
    """Wraps a remote git repository containing a dbt project."""

    repo_url: str
    repo_relative_path: Annotated[
        str,
        Resolver.default(
            description="The relative path to the dbt project within the repository.",
            examples=["dbt/my_dbt_project"],
        ),
    ] = "."
    token: Annotated[
        str | None,
        Resolver.default(
            description="Token for authenticating to the provided repository.",
            examples=["'{{ env.GITHUB_TOKEN }}'"],
        ),
    ] = None
    profile: Annotated[
        str | None,
        Resolver.default(description="The profile to use for the dbt project."),
    ] = None
    target: Annotated[
        str | None,
        Resolver.default(
            description="The target to use for the dbt project.",
            examples=["dev", "prod"],
        ),
    ] = None

    @property
    def defs_state_discriminator(self) -> str:
        return self.repo_url

    def _get_clone_url(self) -> str:
        # in github action environments, the token will be available automatically as an env var
        raw_token = self.token or os.getenv("GITHUB_TOKEN")
        if raw_token is None:
            return self.repo_url
        else:
            # insert the token into the url
            token = quote(raw_token, safe="")
            parts = urlparse(self.repo_url)
            return urlunparse(parts._replace(netloc=f"{token}@{parts.netloc}"))

    def sync(self, state_path: Path) -> None:
        _shallow_clone(
            self._get_clone_url(),
            self._local_project_dir(state_path),
            display_url=self.repo_url,
        )
        project = self.get_project(state_path)
        project.preparer.prepare(project)

    def get_project(self, state_path: Path | None) -> "DbtProject":
        if state_path is None:
            raise DagsterInvalidDefinitionError(
                "Attempted to `get_project()` on a `RemoteGitDbtProjectWrapper` without a path. "
                "This can happen when calling unsupported methods on the `DbtProjectComponent`."
            )

        local_dir = self._local_project_dir(state_path)
        return DbtProject(
            project_dir=local_dir / self.repo_relative_path,
            profile=self.profile,
            target=self.target,
        )
