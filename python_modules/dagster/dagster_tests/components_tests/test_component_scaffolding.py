from typing import Optional

import pytest
from dagster.components.component_scaffolding import parse_params_model
from dagster.components.scaffold.scaffold import NoParams, Scaffolder, scaffold_with
from pydantic import BaseModel, ValidationError


class TestParamsModelWithDefaults(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None


class TestParamsModelWithoutDefaults(BaseModel):
    name: str
    age: int
    is_active: bool


class TestScaffolderWithDefaults(Scaffolder[TestParamsModelWithDefaults]):
    @classmethod
    def get_scaffold_params(cls) -> type[TestParamsModelWithDefaults]:
        return TestParamsModelWithDefaults


class TestScaffolderWithoutDefaults(Scaffolder[TestParamsModelWithoutDefaults]):
    @classmethod
    def get_scaffold_params(cls) -> type[TestParamsModelWithoutDefaults]:
        return TestParamsModelWithoutDefaults


class NoParamsScaffolder(Scaffolder[BaseModel]):
    @classmethod
    def get_scaffold_params(cls) -> type[BaseModel]:
        return NoParams


@scaffold_with(TestScaffolderWithDefaults)
def fn_with_scaffolder_with_defaults() -> None: ...


@scaffold_with(TestScaffolderWithoutDefaults)
def fn_with_scaffolder_without_defaults() -> None: ...


@scaffold_with(NoParamsScaffolder)
def fn_with_no_params_scaffolder() -> None: ...


def test_parse_params_model_no_params() -> None:
    """Test when json_params is None."""
    assert (
        parse_params_model(obj=fn_with_scaffolder_with_defaults, json_params=None)
        == TestParamsModelWithDefaults()
    )
    with pytest.raises(ValidationError) as exc_info:
        assert exc_info
        assert parse_params_model(obj=fn_with_scaffolder_without_defaults, json_params=None)
    assert parse_params_model(obj=fn_with_no_params_scaffolder, json_params=None) == NoParams()


def test_parse_params_model_no_scaffolder() -> None:
    """Test when object has no scaffolder."""

    def no_scaffolder_fn() -> None: ...

    with pytest.raises(Exception) as exc_info:
        parse_params_model(obj=no_scaffolder_fn, json_params='{"name": "test", "age": 30}')
    assert "must be decorated with @scaffold_with" in str(exc_info.value)


def test_parse_params_model_valid_params() -> None:
    """Test when valid JSON params are provided."""
    result = parse_params_model(
        obj=fn_with_scaffolder_with_defaults, json_params='{"name": "test", "age": 30}'
    )
    assert isinstance(result, TestParamsModelWithDefaults)
    assert result.name == "test"
    assert result.age == 30


def test_parse_params_model_empty_params() -> None:
    """Test when no JSON params are provided but scaffolder accepts params."""
    result = parse_params_model(obj=fn_with_scaffolder_with_defaults, json_params="{}")
    assert isinstance(result, TestParamsModelWithDefaults)
    assert result.name is None
    assert result.age is None


def test_parse_params_model_without_defaults_empty_params() -> None:
    """Test when no JSON params are provided and model has required fields."""
    with pytest.raises(ValidationError) as exc_info:
        parse_params_model(obj=fn_with_scaffolder_without_defaults, json_params="{}")
    assert "validation error" in str(exc_info.value).lower()
    assert "field required" in str(exc_info.value).lower()


def test_parse_params_model_without_defaults_valid_params() -> None:
    """Test when valid JSON params are provided for model with required fields."""
    result = parse_params_model(
        obj=fn_with_scaffolder_without_defaults,
        json_params='{"name": "test", "age": 30, "is_active": true}',
    )
    assert isinstance(result, TestParamsModelWithoutDefaults)
    assert result.name == "test"
    assert result.age == 30
    assert result.is_active is True


def test_parse_params_model_no_params_but_provided() -> None:
    """Test when scaffolder doesn't accept params but JSON params are provided."""
    with pytest.raises(Exception) as exc_info:
        parse_params_model(
            obj=fn_with_no_params_scaffolder, json_params='{"name": "test", "age": 30}'
        )
    assert "Input should be null" in str(exc_info.value)


def test_parse_params_model_validation_error() -> None:
    """Test when JSON params fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        parse_params_model(
            obj=fn_with_scaffolder_with_defaults, json_params='{"name": "test", "age": "invalid"}'
        )
    assert "validation error" in str(exc_info.value).lower()


def test_parse_params_model_invalid_json() -> None:
    """Test when invalid JSON is provided."""
    with pytest.raises(ValidationError) as exc_info:
        parse_params_model(obj=fn_with_scaffolder_with_defaults, json_params="invalid json")
    assert "invalid json" in str(exc_info.value).lower()
