from collections import namedtuple

from dagster import check

from .context import PipelineContextDefinition

from .dependency import (
    DependencyDefinition,
    Solid,
    SolidInputHandle,
    SolidInstance,
    SolidOutputHandle,
)

from .expectation import ExpectationDefinition, ExpectationResult

from .infos import ContextCreationExecutionInfo, ExpectationExecutionInfo, TransformExecutionInfo

from .input import InputDefinition

from .output import OutputDefinition

from .resource import ResourceDefinition

from .repository import RepositoryDefinition

from .pipeline import PipelineDefinition, solids_in_topological_order

from .pipeline_creation import create_execution_structure

from .solid import SolidDefinition

from .utils import DEFAULT_OUTPUT


class Result(namedtuple('_Result', 'value output_name')):
    '''A solid transform function return a stream of Result objects.
    An implementator of a SolidDefinition must provide a transform that
    yields objects of this type.

    Attributes:
        value (Any): Value returned by the transform.
        output_name (str): Name of the output returns. defaults to "result"
'''

    def __new__(cls, value, output_name=DEFAULT_OUTPUT):
        return super(Result, cls).__new__(cls, value, check.str_param(output_name, 'output_name'))
