from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from dagster._record import record
from pydantic import BaseModel


@record
class ComponentGenerateRequest:
    component_type_name: str
    component_instance_root_path: Path


class ComponentGenerator:
    @classmethod
    def get_params_schema_type(cls) -> Optional[type[BaseModel]]:
        return None

    @abstractmethod
    def generate_files(self, request: ComponentGenerateRequest, params: Any) -> None: ...


@dataclass
class ComponentGeneratorUnavailableReason:
    message: str


class DefaultComponentGenerator(ComponentGenerator):
    def generate_files(self, request: ComponentGenerateRequest, params: Any) -> None:
        # This will be deleted once all components are converted to the new ComponentGenerator API
        from dagster_components.generate import generate_component_yaml

        generate_component_yaml(request, params.model_dump() if params else {})
