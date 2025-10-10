import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from dagster.components.resolved.base import Resolvable
from dagster_shared.serdes.objects.models.defs_state_info import get_local_state_dir
from git import Repo

from dagster_dbt.dbt_project.dbt_project import DbtProject


class RemoteDbtProject(ABC):
    @abstractmethod
    def fetch(self, key: str) -> None: ...

    @abstractmethod
    def get_dbt_project(self, key: str) -> DbtProject: ...


@dataclass
class RemoteGitDbtProject(RemoteDbtProject, Resolvable):
    repo_url: str
    token: Optional[str] = None
    profile: Optional[str] = None
    repo_relative_path: str = "."

    def _local_path(self, key: str) -> Path:
        return get_local_state_dir(key) / "project"

    def get_dbt_project(self, key: str) -> DbtProject:
        project_path = self._local_path(key) / self.repo_relative_path
        return DbtProject(project_dir=project_path, profile=self.profile)

    def fetch(self, key: str) -> None:
        local_path = self._local_path(key)
        shutil.rmtree(local_path, ignore_errors=True)
        Repo.clone_from(self.repo_url, local_path, depth=1)
