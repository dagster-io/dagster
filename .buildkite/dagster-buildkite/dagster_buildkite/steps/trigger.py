from typing import Dict, List, Optional

from dagster_buildkite.utils import TriggerStep, safe_getenv


def build_trigger_step(
    pipeline: str,
    trigger_branch: str,
    branches: Optional[List[str]] = None,
    async_step: bool = False,
    if_condition: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
) -> TriggerStep:
    """Trigger a build of another pipeline.

    See:
        https://buildkite.com/docs/pipelines/trigger-step

    Args:
        pipeline (str): The pipeline to trigger
        branches (List[str]): List of branches to trigger
        async_step (bool): If set to true the step will immediately continue, regardless of the
            success of the triggered build. If set to false the step will wait for the triggered
            build to complete and continue only if the triggered build passed.
        if_condition (str): A boolean expression that omits the step when false. Cannot be set with
            "branches" also set.
    """
    dagster_commit_hash = safe_getenv("BUILDKITE_COMMIT")
    step: TriggerStep = {
        "trigger": pipeline,
        "label": f":link: {pipeline} from dagster@{dagster_commit_hash[:10]}",
        "async": async_step,
        "build": {
            "env": env or {},
            "branch": trigger_branch,
        },
    }

    if branches:
        step["branches"] = " ".join(branches)

    if if_condition:
        step["if"] = if_condition

    return step
