from typing import List, NamedTuple, Optional


class RepoRelativeTarget(NamedTuple):
    """
    The thing to be executed by a schedule or sensor, selecting by name a pipeline in the same repository.
    """

    pipeline_name: str
    mode: str
    solid_selection: Optional[List[str]]
