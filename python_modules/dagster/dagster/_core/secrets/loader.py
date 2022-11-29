from abc import ABC, abstractmethod
from typing import Mapping, Optional

from dagster._core.instance import MayHaveInstanceWeakref


class SecretsLoader(ABC, MayHaveInstanceWeakref):
    @abstractmethod
    def get_secrets_for_environment(self, location_name: Optional[str]) -> Mapping[str, str]:
        pass

    def dispose(self):
        return
