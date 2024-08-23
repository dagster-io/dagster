from dataclasses import dataclass
from typing import Callable, List, Optional

from dagster import AssetSpec, Definitions, multi_asset

from .def_factory import DefsFactory


@dataclass
class PythonDefs(DefsFactory):
    specs: List[AssetSpec]
    name: str
    group: Optional[str] = None
    python_fn: Optional[Callable] = None

    def build_defs(self) -> Definitions:
        @multi_asset(
            specs=self.specs,
            name=self.name,
            group_name=self.group,
        )
        def _multi_asset():
            if self.python_fn:
                self.python_fn()

        return Definitions(assets=[_multi_asset])
