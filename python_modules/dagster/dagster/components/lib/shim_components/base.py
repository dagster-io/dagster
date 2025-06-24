from abc import abstractmethod

from dagster.components.scaffold.scaffold import Scaffolder, ScaffoldRequest, TModel


class ShimScaffolder(Scaffolder[TModel]):
    @abstractmethod
    def get_text(self, request: ScaffoldRequest[TModel]) -> str: ...

    def scaffold(self, request: ScaffoldRequest[TModel]) -> None:
        if request.target_path.suffix != ".py":
            raise ValueError("Invalid target path suffix. Expected a path ending in `.py`.")
        # temporary hack as currently all scaffold requests target directories
        # that are auto-created
        # TODO this seems extremely dangerous -- schrockn 06-24-2025
        # https://linear.app/dagster-labs/issue/ADOPT-1614/bad-error-and-scary-code-when-scaffolding-shim-components
        request.target_path.rmdir()
        request.target_path.write_text(self.get_text(request))
