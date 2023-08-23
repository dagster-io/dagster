import os
from dataclasses import dataclass

from ._protocol import (
    DAGSTER_EXTERNALS_ENV_KEYS,
)


def get_external_execution_params() -> "ExternalExecutionParams":
    input_path = os.getenv(DAGSTER_EXTERNALS_ENV_KEYS["input"])
    output_path = os.getenv(DAGSTER_EXTERNALS_ENV_KEYS["output"])
    assert input_path, "input_path must be set"
    assert output_path, "output_path must be set"
    return ExternalExecutionParams(
        input_path=input_path,
        output_path=output_path,
    )


@dataclass
class ExternalExecutionParams:
    input_path: str
    output_path: str
