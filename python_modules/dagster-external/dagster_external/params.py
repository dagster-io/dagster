import os
from dataclasses import dataclass
from typing import Optional

from dagster_external.protocol import (
    DAGSTER_EXTERNAL_DEFAULT_HOST,
    DAGSTER_EXTERNAL_DEFAULT_INPUT_MODE,
    DAGSTER_EXTERNAL_DEFAULT_OUTPUT_MODE,
    DAGSTER_EXTERNAL_DEFAULT_PORT,
    DAGSTER_EXTERNAL_ENV_KEYS,
    ExternalExecutionIOMode,
)


def get_external_execution_params() -> "ExternalExecutionParams":
    is_orchestration_active = bool(os.getenv("DAGSTER_EXTERNAL_IS_ORCHESTRATION_ACTIVE"))
    raw_input_mode = os.getenv(
        DAGSTER_EXTERNAL_ENV_KEYS["input_mode"], DAGSTER_EXTERNAL_DEFAULT_INPUT_MODE
    )
    raw_output_mode = os.getenv(
        DAGSTER_EXTERNAL_ENV_KEYS["output_mode"], DAGSTER_EXTERNAL_DEFAULT_OUTPUT_MODE
    )
    return ExternalExecutionParams(
        is_orchestration_active=is_orchestration_active,
        input_mode=ExternalExecutionIOMode[raw_input_mode],
        output_mode=ExternalExecutionIOMode[raw_output_mode],
        input_path=os.getenv(DAGSTER_EXTERNAL_ENV_KEYS["input"]),
        output_path=os.getenv(DAGSTER_EXTERNAL_ENV_KEYS["output"]),
        host=os.getenv(DAGSTER_EXTERNAL_ENV_KEYS["host"], DAGSTER_EXTERNAL_DEFAULT_HOST),
        port=int(os.getenv(DAGSTER_EXTERNAL_ENV_KEYS["port"], DAGSTER_EXTERNAL_DEFAULT_PORT)),
    )


@dataclass
class ExternalExecutionParams:
    is_orchestration_active: bool
    input_mode: str
    output_mode: str
    input_path: Optional[str]
    output_path: Optional[str]
    host: str
    port: int
