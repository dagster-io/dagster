import logging
import subprocess
from dataclasses import dataclass


@dataclass
class GitCommitMetadata:
    timestamp: str
    message: str
    email: str
    name: str


def get_git_commit_metadata(project_dir: str) -> GitCommitMetadata:
    commands = {
        "timestamp": f"git -C {project_dir} log -1 --format=%cd --date=unix".split(),
        "message": f"git -C {project_dir} log -1 --format=%s".split(),
        "email": f"git -C {project_dir} log -1 --format=%ae".split(),
        "name": f"git -C {project_dir} log -1 --format=%an".split(),
    }
    metadata = {}
    for key, command in commands.items():
        logging.debug("Running %r", command)
        proc = subprocess.run(command, capture_output=True, check=False)
        if proc.returncode:
            logging.error(f"git command failed: {proc.stdout}\n{proc.stderr}")
        metadata[key] = proc.stdout.decode("utf-8").strip()

    return GitCommitMetadata(**metadata)
