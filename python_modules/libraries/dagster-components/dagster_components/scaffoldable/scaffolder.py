from abc import abstractmethod
from pathlib import Path
from typing import Any, Optional

from dagster._record import record
from pydantic import BaseModel


@record
class ComponentScaffoldRequest:
    component_type_name: str
    component_instance_root_path: Path


class ComponentScaffolder:
    @classmethod
    def get_schema(cls) -> Optional[type[BaseModel]]:
        return None

    @abstractmethod
    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None: ...
