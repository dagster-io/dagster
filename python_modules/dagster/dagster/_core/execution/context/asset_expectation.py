from dagster._annotations import public
from dagster._core.log_manager import DagsterLogManager


class AssetExpectationContext:
    def __init__(self, value: object, log: DagsterLogManager):
        self._log = log
        self._value = value

    @public
    def load_value(self) -> object:
        return self._value

    @public  # type: ignore
    @property
    def log(self) -> DagsterLogManager:
        return self._log
