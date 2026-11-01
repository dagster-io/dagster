import dagster as dg
import pytest
from dagster._core.definitions.inference import InferredOutputProps
from dagster._core.definitions.metadata import normalize_metadata_value
from dagster._core.definitions.output import OutputDefinition


def test_normalized_text_metadata_keeps_custom_attributes_local() -> None:
    first = normalize_metadata_value("ownership_regression")
    second = normalize_metadata_value("ownership_regression")
    setattr(first, "custom_attribute", "local")
    assert not hasattr(second, "custom_attribute")
    assert first == second


@pytest.mark.parametrize("value", ["ownership_regression", 42, 1.5, True, None])
def test_inferred_output_metadata_keeps_custom_attributes_local(
    value: str | int | float | bool | None,
) -> None:
    inferred = InferredOutputProps(annotation=int, description=None)
    first = OutputDefinition(metadata={"value": value}).combine_with_inferred(inferred)
    second = OutputDefinition(metadata={"value": value}).combine_with_inferred(inferred)
    setattr(first.metadata["value"], "custom_attribute", "local")
    assert not hasattr(second.metadata["value"], "custom_attribute")
    assert first.metadata == second.metadata


def test_explicit_metadata_values_preserve_caller_identity() -> None:
    value = dg.MetadataValue.text("explicit")
    assert normalize_metadata_value(value) is value
