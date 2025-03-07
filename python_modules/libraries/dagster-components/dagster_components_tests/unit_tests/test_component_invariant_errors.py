import pytest
from dagster._check.functions import CheckError
from dagster_components import Component, ComponentLoadContext


def test_component_does_not_implement():
    class AComponent(Component):
        pass

    with pytest.raises(
        CheckError, match="Must inherit from either ResolvableModel or ResolvedFrom"
    ):
        AComponent.load(attributes=None, context=ComponentLoadContext.for_test())
