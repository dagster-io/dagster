from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar

from dagster._record import record


@record
class ComponentGenerateRequest:
    component_type_name: str
    component_instance_root_path: Path


class ComponentGenerator:
    generator_params: ClassVar = None

    @abstractmethod
    def generate_files(self, request: ComponentGenerateRequest, params: Any) -> None: ...


@dataclass
class ComponentGeneratorUnavailableReason:
    message: str
