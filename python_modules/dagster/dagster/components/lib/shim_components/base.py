from abc import abstractmethod
from typing import Any

from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest


class ShimScaffolder(Scaffolder):
    @abstractmethod
    def get_text(self, filename: str, params: Any) -> str: ...
    def scaffold(self, request: ScaffoldRequest, params: Any) -> None:
        if request.target_path.suffix != ".py":
            raise ValueError("Invalid target path suffix. Expected a path ending in `.py`.")
        # temporary hack as currently all scaffold requests target directories
        # that are auto-created
        request.target_path.rmdir()
        request.target_path.write_text(self.get_text(request.target_path.stem, params))
