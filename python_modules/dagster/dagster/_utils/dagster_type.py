from typing import Any

from dagster._core.definitions.events import Failure, TypeCheck
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.job_base import InMemoryJob
from dagster._core.errors import DagsterInvariantViolationError
from dagster._core.execution.api import create_execution_plan
from dagster._core.execution.context_creation_job import scoped_job_context
from dagster._core.instance import DagsterInstance
from dagster._core.types.dagster_type import resolve_dagster_type
from dagster._utils.typing_api import is_typing_type


def check_dagster_type(dagster_type: Any, value: Any) -> TypeCheck:
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
            f"Must pass in a type from dagster module. You passed {dagster_type} "
            "which is part of python's typing module."
        )

    dagster_type = resolve_dagster_type(dagster_type)

    job = InMemoryJob(GraphDefinition(node_defs=[], name="empty").to_job())
    job_def = job.get_definition()

    instance = DagsterInstance.ephemeral()
    execution_plan = create_execution_plan(job)
    dagster_run = instance.create_run_for_job(job_def)
    with scoped_job_context(execution_plan, job, {}, dagster_run, instance) as context:
        type_check_context = context.for_type(dagster_type)
        try:
            type_check = dagster_type.type_check(type_check_context, value)
        except Failure as failure:
            return TypeCheck(success=False, description=failure.description)

        if not isinstance(type_check, TypeCheck):
            raise DagsterInvariantViolationError(
                f"Type checks can only return TypeCheck. Type {dagster_type.display_name} returned {type_check!r}."
            )
        return type_check
