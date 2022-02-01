from typing import List, NamedTuple, Optional

from dagster import check
from dagster.core.code_pointer import CodePointer
from dagster.serdes import create_snapshot_id, whitelist_for_serdes
from dagster.utils import frozenlist

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
            ("entry_point", Optional[List[str]]),
        ],
    ),
):
    """
    Derived from the handle structure in the host process, this is the subset of information
    necessary to load a target RepositoryDefinition in a "user process" locally.

    Args:
      executable_path (str): The Python executable of the user process.
      code_pointer (CodePoitner): Once the process has started, an object that can be used to
          find and load the repository in code.
      container_image (Optinonal[str]): The image to use when creating a new container that
          loads the repository. Only used in execution environments that start containers.
      entry_point (Optional[List[str]]): The entry point to use when starting a new process
          to load the repository. Defaults to ["dagster"] (and may differ from the executable_path).
    """

    def __new__(cls, executable_path, code_pointer, container_image=None, entry_point=None):
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
        )

    def get_id(self):
        return create_snapshot_id(self)

    def get_pipeline_origin(self, pipeline_name):
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

    def get_id(self):
        return create_snapshot_id(self)

    @property
    def executable_path(self):
        return self.repository_origin.executable_path

    def get_repo_pointer(self) -> CodePointer:
        return self.repository_origin.code_pointer
