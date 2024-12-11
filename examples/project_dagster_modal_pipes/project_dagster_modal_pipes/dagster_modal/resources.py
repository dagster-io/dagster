from pathlib import Path
from typing import Mapping, Optional, Union

from dagster import OpExecutionContext, PipesSubprocessClient
from dagster._annotations import public
from dagster._core.pipes.client import PipesClientCompletedInvocation
from dagster_pipes import PipesExtras


class ModalClient(PipesSubprocessClient):
    def __init__(
        self,
        project_directory: Optional[Union[str, Path]] = None,
        env: Optional[Mapping[str, str]] = None,
    ):
        if isinstance(project_directory, Path):
            project_directory = str(project_directory)
        super().__init__(env=env, cwd=project_directory)

    @public
    def deploy(
        self,
        *,
        app_ref: str,
        name: Optional[str] = None,
        tag: Optional[str] = None,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> PipesClientCompletedInvocation:
        command = ["modal", "deploy", app_ref]

        if name:
            command += ["--name", name]

        if tag:
            command += ["--tag", tag]

        return super().run(
            command=command,
            context=context,
            extras=extras,
            env=env,
        )

    @public
    def run(
        self,
        *,
        func_ref: str,
        context: OpExecutionContext,
        extras: Optional[PipesExtras] = None,
        env: Optional[Mapping[str, str]] = None,
    ) -> PipesClientCompletedInvocation:
        return super().run(
            command=["modal", "run", func_ref],
            context=context,
            extras=extras,
            env=env,
        )
