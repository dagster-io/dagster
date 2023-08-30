from .._protocol import (
    ExternalExecutionContextData,
)
from .._util import param_from_env_var
from .base import ExternalExecutionContextLoader


class ExternalExecutionEnvContextLoader(ExternalExecutionContextLoader):
    def load_context(self) -> ExternalExecutionContextData:
        data = param_from_env_var("context")
        return data["context_data"]
