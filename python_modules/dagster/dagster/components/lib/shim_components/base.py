from abc import abstractmethod
from typing import Optional

from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest, TModel


class ShimScaffolder(Scaffolder[TModel]):
    @abstractmethod
    def get_text(self, filename: str, params: Optional[TModel]) -> str: ...


def scaffold_text(
    scaffolder: ShimScaffolder[TModel], request: ScaffoldRequest, params: Optional[TModel] = None
) -> None:
    if request.target_path.suffix != ".py":
        raise ValueError("Invalid target path suffix. Expected a path ending in `.py`.")
    # temporary hack as currently all scaffold requests target directories
    # that are auto-created
    request.target_path.rmdir()
    request.target_path.write_text(scaffolder.get_text(request.target_path.stem, params))
