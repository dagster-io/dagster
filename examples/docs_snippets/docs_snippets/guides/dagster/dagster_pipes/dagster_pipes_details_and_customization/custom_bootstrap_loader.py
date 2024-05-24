### EXTERNAL PROCESS

from cloud_service import METADATA  # type: ignore
from dagster_pipes import (
    DAGSTER_PIPES_CONTEXT_ENV_VAR,
    DAGSTER_PIPES_MESSAGES_ENV_VAR,
    PipesParams,
    PipesParamsLoader,
)


class MyCustomParamsLoader(PipesParamsLoader):
    def is_dagster_pipes_process(self) -> bool:
        return DAGSTER_PIPES_CONTEXT_ENV_VAR in METADATA

    def load_context_params(self) -> PipesParams:
        return METADATA[DAGSTER_PIPES_CONTEXT_ENV_VAR]

    def load_messages_params(self) -> PipesParams:
        return METADATA[DAGSTER_PIPES_MESSAGES_ENV_VAR]
