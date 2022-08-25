from dagster._core.definitions.events import Failure, TypeCheck
from dagster._core.definitions.pipeline_base import InMemoryPipeline
from dagster._core.definitions.pipeline_definition import PipelineDefinition
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context_creation_pipeline import scoped_pipeline_context
from dagster._core.instance import DagsterInstance
from dagster._core.types.dagster_type import resolve_dagster_type

from .typing_api import is_typing_type


def check_dagster_type(dagster_type, value):
    """Test a custom Dagster type.

    Args:
        dagster_type (Any): The Dagster type to test. Should be one of the
            :ref:`built-in types <builtin>`, a dagster type explicitly constructed with
            :py:func:`as_dagster_type`, :py:func:`@usable_as_dagster_type <dagster_type>`, or
            :py:func:`PythonObjectDagsterType`, or a Python type.
        value (Any): The runtime value to test.

    Returns:
        TypeCheck: The result of the type check.


    Examples:

        .. code-block:: python

            assert check_dagster_type(Dict[Any, Any], {'foo': 'bar'}).success
    """

    if is_typing_type(dagster_type):
        raise DagsterInvariantViolationError(
            (
                "Must pass in a type from dagster module. You passed {dagster_type} "
                "which is part of python's typing module."
            ).format(dagster_type=dagster_type)
        )

    dagster_type = resolve_dagster_type(dagster_type)

    pipeline = InMemoryPipeline(PipelineDefinition([], "empty"))
    pipeline_def = pipeline.get_definition()

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(pipeline)
    pipeline_run = instance.create_run_for_pipeline(pipeline_def)
    with scoped_pipeline_context(execution_plan, pipeline, {}, pipeline_run, instance) as context:
        context = context.for_type(dagster_type)
        try:
            type_check = dagster_type.type_check(context, value)
        except Failure as failure:
            return TypeCheck(success=False, description=failure.description)

        if not isinstance(type_check, TypeCheck):
            raise DagsterInvariantViolationError(
                "Type checks can only return TypeCheck. Type {type_name} returned {value}.".format(
                    type_name=dagster_type.display_name, value=repr(type_check)
                )
            )
        return type_check
