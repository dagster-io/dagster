### EXTERNAL PROCESS

from cloud_service import METADATA  # type: ignore
from dagster_pipes import (
    PIPES_CONTEXT_KEY,
    PIPES_DATA_ENV_VAR,
    PIPES_MESSAGE_WRITER_PARAMS_KEY,
    PipesParams,
    PipesParamsLoader,
)


class MyCustomParamsLoader(PipesParamsLoader):
    def is_dagster_pipes_process(self) -> bool:
        return PIPES_DATA_ENV_VAR in METADATA

    def load_context_params(self) -> PipesParams:
        return METADATA[PIPES_DATA_ENV_VAR][PIPES_CONTEXT_KEY]

    def load_messages_params(self) -> PipesParams:
        return METADATA[PIPES_DATA_ENV_VAR][PIPES_MESSAGE_WRITER_PARAMS_KEY]
