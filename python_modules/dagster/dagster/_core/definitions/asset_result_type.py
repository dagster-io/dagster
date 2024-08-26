from typing import Literal

from .asset_spec import AssetExecutionType

AssetResultType = Literal["materialize", "observe", "unexecutable"]


def asset_execution_type_from_result_type(result_type: AssetResultType) -> AssetExecutionType:
    return {
        "materialize": AssetExecutionType.MATERIALIZATION,
        "observe": AssetExecutionType.OBSERVATION,
        "unexecutable": AssetExecutionType.UNEXECUTABLE,
    }[result_type]
