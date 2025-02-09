from dagster_components.core.component import ComponentLoadContext
from dagster_components.core.resolution_engine.context import ResolutionContext
from dagster_components.lib.test.nested_resolved import (
    BusinessObjectOne,
    BusinessObjectTwo,
    BusinessObjectZero,
    LevelOneSchema,
    LevelTwoSchema,
    LevelZeroSchema,
    NestedResolvedComponent,
    ResolvedLevelOne,
    ResolvedLevelTwo,
    ResolvedLevelZero,
)


def test_schema_construction() -> None:
    schema = LevelZeroSchema(
        level_zero="zero",
        sub_schema=LevelOneSchema(level_one="one", sub_schema=LevelTwoSchema(level_two="two")),
    )
    assert schema.level_zero == "zero"
    assert schema.sub_schema.level_one == "one"
    assert schema.sub_schema.sub_schema.level_two == "two"


def test_resolution_level_two() -> None:
    output = ResolvedLevelTwo(LevelTwoSchema(level_two="two")).resolve(ResolutionContext.default())
    assert isinstance(output, BusinessObjectTwo)
    assert output.level_two == "two_computed"


def test_resolution_level_one() -> None:
    output = ResolvedLevelOne(
        LevelOneSchema(level_one="one", sub_schema=LevelTwoSchema(level_two="two"))
    ).resolve(ResolutionContext.default())
    assert isinstance(output, BusinessObjectOne)
    assert output.level_one == "one_computed"
    assert output.sub_schema.level_two == "two_computed"


def test_resolution_level_zero() -> None:
    zero_schema = LevelZeroSchema(
        level_zero="zero",
        sub_schema=LevelOneSchema(level_one="one", sub_schema=LevelTwoSchema(level_two="two")),
    )

    output = ResolvedLevelZero(zero_schema).resolve(ResolutionContext.default())
    assert isinstance(output, BusinessObjectZero)
    assert output.level_zero == "zero_computed"
    assert isinstance(output.sub_schema, BusinessObjectOne)


def test_nested_component_construction() -> None:
    zero_schema = LevelZeroSchema(
        level_zero="zero",
        sub_schema=LevelOneSchema(level_one="one", sub_schema=LevelTwoSchema(level_two="two")),
    )
    component = NestedResolvedComponent.load(
        params=zero_schema, context=ComponentLoadContext.for_test()
    )

    assert isinstance(component, NestedResolvedComponent)

    assert component.level_zero == "zero_computed"
    assert component.sub_schema.level_one == "one_computed"
