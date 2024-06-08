from abc import ABC, abstractmethod
from typing import Literal, Mapping, Optional, Sequence, Type, TypeVar, Union

from dagster._builtins import Nothing
from dagster._core.definitions.decorators.op_decorator import op
from dagster._core.definitions.dependency import DependencyDefinition, MultiDependencyDefinition
from dagster._core.definitions.graph_definition import GraphDefinition
from dagster._core.definitions.input import In
from dagster._core.definitions.job_definition import JobDefinition
from dagster._core.definitions.op_definition import OpDefinition
from dagster._core.definitions.output import Out
from dagster._core.definitions.policy import Backoff, Jitter, RetryPolicy
from dagster._core.execution.context.compute import OpExecutionContext
from dagster._model import DagsterModel

from dagster_blueprints.blueprint import Blueprint, BlueprintDefinitions

DEFAULT_INPUT_NAME = "_start_after"


class RetryPolicyModel(DagsterModel):
    max_retries: int
    delay: Optional[Union[int, float]] = None
    backoff: Optional[Backoff] = None
    jitter: Optional[Jitter] = None

    def to_retry_policy(self) -> RetryPolicy:
        return RetryPolicy(
            max_retries=self.max_retries, delay=self.delay, backoff=self.backoff, jitter=self.jitter
        )


class OpModel(DagsterModel, ABC):
    retry_policy: Optional[RetryPolicyModel] = None
    deps: Sequence[str] = []

    def build_op(self, name: str) -> OpDefinition:
        @op(
            name=name,
            ins={DEFAULT_INPUT_NAME: In(dagster_type=Nothing)},
            out=Out(Nothing),
            retry_policy=self.retry_policy.to_retry_policy() if self.retry_policy else None,
        )
        def _op(context: OpExecutionContext, **kwargs) -> None:
            self.compute_fn(context=context)

        return _op

    @abstractmethod
    def compute_fn(self, context: OpExecutionContext) -> None:
        raise NotImplementedError()


T_OpModel = TypeVar("T_OpModel", bound=OpModel)


def make_op_job_blueprint_type(op_model_type: Type[T_OpModel]) -> Type[Blueprint]:
    class OpJobBlueprint(Blueprint):
        type: Literal["op_job"] = "op_job"
        name: str
        ops: Mapping[str, op_model_type]

        def build_defs(self) -> BlueprintDefinitions:
            op_defs = [
                op_model.build_op(self._scope_op_name_to_job(name))
                for name, op_model in self.ops.items()
            ]
            graph_deps_dict = {
                self._scope_op_name_to_job(name): {
                    DEFAULT_INPUT_NAME: MultiDependencyDefinition(
                        [
                            DependencyDefinition(self._scope_op_name_to_job(dep_name))
                            for dep_name in op_model.deps
                        ]
                    )
                }
                for name, op_model in self.ops.items()
            }

            graph_def = GraphDefinition(
                name=self.name, node_defs=op_defs, dependencies=graph_deps_dict
            )
            job_def = JobDefinition(name=self.name, graph_def=graph_def)
            return BlueprintDefinitions(jobs=[job_def])

        def _scope_op_name_to_job(self, op_name) -> str:
            """Since ops are required to have unique names within a repo, this scopes op names to the
            job that they're contained in.
            """
            return f"{op_name}__{self.name}"

    return OpJobBlueprint


class ShellCommandOpModel(OpModel):
    type: Literal["shell_command_op"] = "shell_command_op"
    command: Union[str, Sequence[str]]
    env: Optional[Mapping[str, str]] = None
    cwd: Optional[str] = None

    def compute_fn(self, context: OpExecutionContext) -> None:
        context.resources.pipes_subprocess_client.run(
            context=context, env=self.env, cwd=self.cwd, command=self.command
        )
