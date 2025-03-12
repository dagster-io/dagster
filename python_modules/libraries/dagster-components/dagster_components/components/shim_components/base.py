from abc import abstractmethod

from dagster_components import Component, Scaffolder, ScaffoldRequest


class ShimScaffolder(Scaffolder):
    @abstractmethod
    def get_text(self) -> str: ...
    def scaffold(self, request: ScaffoldRequest, params: None) -> None:
        if request.target_path.suffix != ".py":
            raise ValueError("Invalid target path suffix. Expected a path ending in `.py`.")
        # temporary hack as currently all scaffold requests target directories
        # that are auto-created
        request.target_path.rmdir()
        request.target_path.write_text(self.get_text())


class ShimComponent(Component):
    """A component that will never be loaded independently. This exists purely as a vessel
    for the @scaffoldable decorator so that the dagster-dg CLI can know about and invoke
    commands against it. In the near future, we'll improve the CLI such that it can handle
    arbitrary scaffoldable objects so that this hack is no longer necessary.
    """

    def build_defs(self, context):
        raise NotImplementedError("Shim components should never be loaded.")
