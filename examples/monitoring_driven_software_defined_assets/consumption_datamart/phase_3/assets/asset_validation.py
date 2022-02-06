from dataclasses import dataclass

from dagster import TypeCheck, DagsterType, Failure


class AssetValidationResult:

    def __init__(self, success, message):
        self._success = success
        self._message = message

        if not success:
            raise Failure(f"Asset Validation failed with: {message}")

    @property
    def success(self) -> bool:
        return self._success

    @property
    def message(self) -> str:
        return self._message


def _dagster_type_check(_, value):
    if not isinstance(value, AssetValidationResult):
        return TypeCheck(
            success=False,
            description="Must be a AssetValidationResult. Got value of type: {type_name}".format(
                type_name=type(value).__name__
            ),
        )

    return TypeCheck(
        success=True,
        metadata={
            'success': str(value.success),
            'message': str(value.message)
        }
    )


AssetValidationResultType = DagsterType(
    name="AssetValidationResult",
    description="Description of Asset Validation Result class",
    type_check_fn=_dagster_type_check
)

