from abc import abstractmethod
from dataclasses import dataclass
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
    def get_params_schema_type(cls) -> Optional[type[BaseModel]]:
        return None

    @abstractmethod
    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None: ...


@dataclass
class ComponentScaffolderUnavailableReason:
    message: str


class DefaultComponentScaffolder(ComponentScaffolder):
    def scaffold(self, request: ComponentScaffoldRequest, params: Any) -> None:
        # This will be deleted once all components are converted to the new ComponentScaffolder API
        from dagster_components.scaffold import scaffold_component_yaml

        scaffold_component_yaml(request, params.model_dump() if params else {})
