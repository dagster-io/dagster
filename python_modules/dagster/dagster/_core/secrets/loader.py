from abc import ABC, abstractmethod
from typing import Dict, Optional

from dagster._core.instance import MayHaveInstanceWeakref


class SecretsLoader(ABC, MayHaveInstanceWeakref):
    @abstractmethod
    def get_secrets_for_environment(self, location_name: Optional[str]) -> Dict[str, str]:
        pass

    def dispose(self):
        return
