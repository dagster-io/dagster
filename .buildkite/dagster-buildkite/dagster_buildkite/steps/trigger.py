import os
import subprocess
from typing import Dict, List, Optional


def trigger_step(
    pipeline: str,
    branches: Optional[List[str]] = None,
    async_step: bool = False,
    if_condition: str = None,
) -> Dict:
    """trigger_step: Trigger a build of another pipeline. See:

        https://buildkite.com/docs/pipelines/trigger-step

    Parameters:
        pipeline (str): The pipeline to trigger
        branches (List[str]): List of branches to trigger
        async_step (bool): If set to true the step will immediately continue, regardless of the
            success of the triggered build. If set to false the step will wait for the triggered
            build to complete and continue only if the triggered build passed.
        if_condition (str): A boolean expression that omits the step when false. Cannot be set with
            "branches" also set.
    """
    commit = (
        subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode("utf-8").strip()
    )
    step = {
        "trigger": pipeline,
        "label": f":link: {pipeline} from dagster@{commit}",
        "async": async_step,
        "build": {
            "env": {
                "DAGSTER_BRANCH": os.getenv("BUILDKITE_BRANCH"),
                "DAGSTER_COMMIT_HASH": os.getenv("BUILDKITE_COMMIT"),
            },
        },
    }

    if branches:
        step["branches"] = " ".join(branches)

    if if_condition:
        step["if"] = if_condition

    return step
