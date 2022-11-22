from typing import Any, List, Mapping, NamedTuple, Optional, Sequence

import dagster._check as check
from dagster._core.code_pointer import CodePointer
from dagster._serdes import create_snapshot_id, whitelist_for_serdes
from dagster._utils import frozenlist

DEFAULT_DAGSTER_ENTRY_POINT = frozenlist(["dagster"])


def get_python_environment_entry_point(executable_path: str) -> List[str]:
    return frozenlist([executable_path, "-m", "dagster"])


@whitelist_for_serdes
class RepositoryPythonOrigin(
    NamedTuple(
        "_RepositoryPythonOrigin",
        [
            ("executable_path", str),
            ("code_pointer", CodePointer),
            ("container_image", Optional[str]),
            ("entry_point", Optional[Sequence[str]]),
            ("container_context", Optional[Mapping[str, Any]]),
        ],
    ),
):
    """
    Args:
      executable_path (str): The Python executable of the user process.
      code_pointer (CodePoitner): Once the process has started, an object that can be used to
          find and load the repository in code.
      container_image (Optinonal[str]): The image to use when creating a new container that
          loads the repository. Only used in execution environments that start containers.
      entry_point (Optional[List[str]]): The entry point to use when starting a new process
          to load the repository. Defaults to ["dagster"] (and may differ from the executable_path).
      container_context (Optional[Dict[str, Any]]): Additional context to use when creating a new
          container that loads the repository. Keys can be specific to a given compute substrate
          (for example, "docker", "k8s", etc.)
    """

    def __new__(
        cls,
        executable_path,
        code_pointer,
        container_image=None,
        entry_point=None,
        container_context=None,
    ):
        return super(RepositoryPythonOrigin, cls).__new__(
            cls,
            check.str_param(executable_path, "executable_path"),
            check.inst_param(code_pointer, "code_pointer", CodePointer),
            check.opt_str_param(container_image, "container_image"),
            (
                frozenlist(check.list_param(entry_point, "entry_point", of_type=str))
                if entry_point != None
                else None
            ),
            (
                check.opt_dict_param(container_context, "container_context")
                if container_context != None
                else None
            ),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)

    def get_pipeline_origin(self, pipeline_name: str) -> "PipelinePythonOrigin":
        check.str_param(pipeline_name, "pipeline_name")
        return PipelinePythonOrigin(pipeline_name, self)


@whitelist_for_serdes
class PipelinePythonOrigin(
    NamedTuple(
        "_PipelinePythonOrigin",
        [
            ("pipeline_name", str),
            ("repository_origin", RepositoryPythonOrigin),
        ],
    )
):
    def __new__(cls, pipeline_name: str, repository_origin: RepositoryPythonOrigin):
        return super(PipelinePythonOrigin, cls).__new__(
            cls,
            check.str_param(pipeline_name, "pipeline_name"),
            check.inst_param(repository_origin, "repository_origin", RepositoryPythonOrigin),
        )

    def get_id(self) -> str:
        return create_snapshot_id(self)

    @property
    def executable_path(self) -> str:
        return self.repository_origin.executable_path

    def get_repo_pointer(self) -> CodePointer:
        return self.repository_origin.code_pointer
