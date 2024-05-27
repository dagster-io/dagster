from abc import ABC, abstractmethod
from typing import Generic, Literal, Mapping, Optional, Sequence, TypeVar, Union

from dagster._core.blueprint import Blueprint, BlueprintDefinitions
from dagster._core.context.compute import OpExecutionContext
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.dependency import DependencyDefinition, MultiDependencyDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.input import In
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.policy import Backoff, Jitter
from dagster._model import DagsterModel


class RetryPolicyModel(DagsterModel):
    max_retries: int
    delay: Optional[Union[int, float]] = None
    backoff: Optional[Backoff] = None
    jitter: Optional[Jitter] = None


class OpModel(DagsterModel, ABC):
    deps: Sequence[str]
    retry_policy: RetryPolicyModel

    @abstractmethod
    def build_op(self) -> OpDefinition:
        pass


T_OpModel = TypeVar("T_OpModel", bound=OpModel)


class OpJobBlueprint(Blueprint, Generic[T_OpModel]):
    type: Literal["op_job"] = "op_job"
    name: str
    ops: Mapping[str, T_OpModel]

    def build_defs(self) -> BlueprintDefinitions:
        op_defs = [
            op_model.build_op().with_replaced_properties(
                name=f"{self.name}_{name}", ins={"in": In()}
            )
            for name, op_model in self.ops.items()
        ]
        graph_deps_dict = {
            name: {
                "in": MultiDependencyDefinition(
                    [DependencyDefinition(dep_name) for dep_name in op_model.deps]
                )
            }
            for name, op_model in self.ops.items()
        }

        graph_def = GraphDefinition(name=self.name, node_defs=op_defs, dependencies=graph_deps_dict)
        job_def = JobDefinition(name=self.name, graph_def=graph_def)
        return BlueprintDefinitions(jobs=[job_def])


class ShellCommandOpModel(OpModel):
    type: Literal["shell_command_op"] = "shell_command_op"
    command: Union[str, Sequence[str]]
    env: Optional[Mapping[str, str]] = None
    cwd: Optional[str] = None

    def build_op(self) -> OpDefinition:
        @op
        def _op(context: OpExecutionContext) -> None:
            context.resources.pipes_subprocess_client.run(
                context=context, env=self.env, cwd=self.cwd, command=self.command
            )

        return _op
