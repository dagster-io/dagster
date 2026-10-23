import pandas as pd
import pytest
from dagster_pandas.constraints import (
    CONSTRAINT_METADATA_KEY,
    ColumnAggregateConstraintWithMetadata,
    ConstraintWithMetadataException,
    all_unique_validator,
)


@pytest.mark.parametrize("values", [["repeat", "repeat"], [7, 7], [False, False]])
@pytest.mark.parametrize("include_actual", [True, False])
@pytest.mark.parametrize("raise_exception", [True, False])
def test_aggregate_failures_preserve_scalar_metadata(
    values: list, include_actual: bool, raise_exception: bool
) -> None:
    """Report invalid columns in either failure mode, with or without explicit actual data."""
    frame = pd.DataFrame({"value": values})
    validator = all_unique_validator if include_actual else lambda column: (False, {})
    constraint = ColumnAggregateConstraintWithMetadata(
        "Confirms unique values",
        validator,
        ConstraintWithMetadataException,
        raise_or_typecheck=raise_exception,
    )
    expected = {"value": values[1:] if include_actual else values}

    if raise_exception:
        with pytest.raises(ConstraintWithMetadataException) as exc:
            constraint.validate(frame, "value")
        assert exc.value.actual == expected
    else:
        result = constraint.validate(frame, "value")
        assert not result.success
        assert result.metadata[CONSTRAINT_METADATA_KEY].data["actual"] == expected
