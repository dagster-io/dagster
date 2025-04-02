from abc import abstractmethod

from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest


class ShimScaffolder(Scaffolder):
    @abstractmethod
    def get_text(self, filename: str) -> str: ...
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        if request.target_path.suffix != ".py":
            raise ValueError("Invalid target path suffix. Expected a path ending in `.py`.")
        # temporary hack as currently all scaffold requests target directories
        # that are auto-created
        request.target_path.rmdir()
        request.target_path.write_text(self.get_text(request.target_path.stem))
