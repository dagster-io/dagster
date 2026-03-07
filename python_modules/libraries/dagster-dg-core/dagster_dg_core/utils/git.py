import logging
import subprocess


def get_local_branch_name(project_dir: str) -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=project_dir,
                stderr=subprocess.PIPE,
            )
            .decode("utf-8")
            .strip()
        )
    except subprocess.SubprocessError:
        logging.getLogger("dg").debug("Failed to determine git branch", exc_info=True)
        return None
