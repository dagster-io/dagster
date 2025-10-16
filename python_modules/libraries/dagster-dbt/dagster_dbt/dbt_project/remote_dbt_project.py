import os
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Optional
from urllib.parse import quote, urlparse, urlunparse

from dagster.components.resolved.base import Resolvable
from dagster.components.resolved.model import Resolver
from dagster.components.utils.project_paths import get_local_state_dir
from git import Repo

from dagster_dbt.dbt_project.dbt_project import DbtProject


class RemoteDbtProject(ABC):
    @abstractmethod
    def fetch(self, local_dir: Path) -> None: ...

    @abstractmethod
    def get_dbt_project(self, local_dir: Path) -> DbtProject: ...


@dataclass
class RemoteGitDbtProject(RemoteDbtProject, Resolvable):
    repo_url: str
    profile: Annotated[
        Optional[str],
        Resolver.default(description="The profile to use for the dbt project."),
    ] = None
    target: Annotated[
        Optional[str],
        Resolver.default(
            description="The target to use for the dbt project.",
            examples=["dev", "prod"],
        ),
    ] = None
    repo_relative_path: Annotated[
        str,
        Resolver.default(
            description="The relative path to the dbt project within the repository.",
            examples=["dbt/my_dbt_project"],
        ),
    ] = "."
    token: Annotated[
        Optional[str],
        Resolver.default(
            description="Token for authenticating to the provided repository.",
            examples=["'{{ env.GITHUB_TOKEN }}'"],
        ),
    ] = None

    def _local_path(self, key: str, project_root: Path) -> Path:
        return get_local_state_dir(key, project_root) / "project"

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

    def get_dbt_project(self, local_dir: Path) -> DbtProject:
        project_path = local_dir / self.repo_relative_path
        return DbtProject(project_dir=project_path, profile=self.profile, target=self.target)

    def fetch(self, local_dir: Path) -> None:
        shutil.rmtree(local_dir, ignore_errors=True)
        Repo.clone_from(self._get_clone_url(), local_dir, depth=1)
