from abc import ABC, abstractmethod
from typing import Mapping, Optional

from dagster._core.instance import T_DagsterInstance, MayHaveInstanceWeakref


class SecretsLoader(ABC, MayHaveInstanceWeakref[T_DagsterInstance]):
    @abstractmethod
    def get_secrets_for_environment(self, location_name: Optional[str]) -> Mapping[str, str]:
        pass

    def dispose(self):
        return
