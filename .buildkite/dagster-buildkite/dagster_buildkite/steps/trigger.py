import subprocess
from typing import Dict, List, Optional


def trigger_step(
    pipeline: str, branches: Optional[List[str]] = None, async_step: bool = False
) -> Dict:
    """trigger_step: Trigger a build of another pipeline.

    Parameters:
        pipeline (str): The pipeline to trigger
        branches (List[str]): List of branches to trigger
        async_step (bool): If set to true the step will immediately continue, regardless of the
            success of the triggered build. If set to false the step will wait for the triggered
            build to complete and continue only if the triggered build passed.
    """
    commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
    step = {
        "trigger": pipeline,
        "label": f":link: {pipeline} from dagster@{commit}",
        "async": async_step,
        "branches": " ".join(branches) if branches else "*",
    }

    return step
