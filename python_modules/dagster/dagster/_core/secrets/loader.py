from abc import ABC, abstractmethod
from collections.abc import Mapping

from dagster._core.instance import MayHaveInstanceWeakref, T_DagsterInstance


class SecretsLoader(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    @abstractmethod
    def get_secrets_for_environment(self, location_name: str | None) -> Mapping[str, str]:
        pass

    def dispose(self):
        return
