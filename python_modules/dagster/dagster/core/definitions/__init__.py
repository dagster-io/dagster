from collections import namedtuple
import re

from dagster import check
from dagster.core import types
from dagster.utils.logging import (
    level_from_string,
    define_colored_console_logger,
)

from dagster.core.errors import (
    DagsterInvalidDefinitionError,
    DagsterInvariantViolationError,
)

from dagster.core.execution_context import (
    RuntimeExecutionContext,
    ExecutionContext,
)

from dagster.core.system_config.objects import DEFAULT_CONTEXT_NAME

from dagster.core.types import (
    Field,
)

from .context import (
    default_pipeline_context_definitions,
    PipelineContextDefinition,
)

from .dependency import (
    DependencyDefinition,
    DependencyStructure,
    Solid,
    SolidInputHandle,
    SolidInstance,
    SolidOutputHandle,
)

from .expectation import (
    ExpectationDefinition,
    ExpectationResult,
)

from .infos import (
    ContextCreationExecutionInfo,
    ExpectationExecutionInfo,
    TransformExecutionInfo,
)

from .input import InputDefinition

from .output import OutputDefinition

from .resource import ResourceDefinition

from .repository import RepositoryDefinition

from .pipeline import (
    PipelineDefinition,
    solids_in_topological_order,
)

from .pipeline_creation import create_execution_structure, construct_type_dictionary

from .solid import SolidDefinition

from .utils import (
    DEFAULT_OUTPUT,
    check_opt_two_dim_dict,
    check_opt_two_dim_str_dict,
    check_two_dim_dict,
    check_two_dim_str_dict,
    check_valid_name,
)


class Result(namedtuple('_Result', 'value output_name')):
    '''A solid transform function return a stream of Result objects.
    An implementator of a SolidDefinition must provide a transform that
    yields objects of this type.

    Attributes:
        value (Any): Value returned by the transform.
        output_name (str): Name of the output returns. defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(
            cls,
            value,
            check.str_param(output_name, 'output_name'),
        )
