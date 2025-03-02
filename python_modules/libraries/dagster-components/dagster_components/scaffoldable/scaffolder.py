from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dagster._record import record
from pydantic import BaseModel


@dataclass
class ScaffolderUnavailableReason:
    message: str


@record
class ScaffoldRequest:
    # fully qualified class name of the scaffolded class
    type_name: str
    # target path for the scaffold request. Typically used to construct absolute paths
    target_path: Path


class Scaffolder:
    @classmethod
    def get_scaffold_params(cls) -> Optional[type[BaseModel]]:
        return None

    @abstractmethod
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None: ...
