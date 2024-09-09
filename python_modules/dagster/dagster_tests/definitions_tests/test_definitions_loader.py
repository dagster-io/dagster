import pytest
from dagster._core.definitions.decorators.definitions_decorator import definitions
from dagster._core.definitions.definitions_class import Definitions
from dagster._core.definitions.definitions_loader import DefinitionsLoadContext
from dagster._core.errors import DagsterInvalidInvocationError


def test_invoke_definitions_loader_with_context():
    @definitions
    def defs(context: DefinitionsLoadContext) -> Definitions:
        return Definitions()

    assert defs(DefinitionsLoadContext())

    with pytest.raises(DagsterInvalidInvocationError, match="requires a DefinitionsLoadContext"):
        defs()


def test_invoke_definitions_loader_no_context():
    @definitions
    def defs() -> Definitions:
        return Definitions()

    assert defs()

    with pytest.raises(DagsterInvalidInvocationError, match="Passed a DefinitionsLoadContext"):
        defs(DefinitionsLoadContext())
