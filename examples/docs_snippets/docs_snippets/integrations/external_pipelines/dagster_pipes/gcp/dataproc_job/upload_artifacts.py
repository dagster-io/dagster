# this script can be used to pack and upload a python .pex file to an gcs bucket
# requires docker and gsutil

import argparse
import os
import subprocess
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

REQUIREMENTS_TXT = SCRIPT_DIR / "requirements.txt"
DAGSTER_DIR = (
    Path(*SCRIPT_DIR.parts[: SCRIPT_DIR.parts.index("dagster-io")])
    / "dagster-io/dagster"
)

parser = argparse.ArgumentParser(description="Build & upload a PEX executable to GCS")
parser.add_argument(
    "--gcs-dir",
    type=str,
    help="gcs directory to copy files into",
)


def main():
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        subprocess.run(
            " && \\\n".join(
                [
                    f"DOCKER_BUILDKIT=1 docker build --output type=local,dest=./output -f {SCRIPT_DIR}/dev.Dockerfile {DAGSTER_DIR}",
                    f"gsutil cp ./output/venv.pex {os.path.join(args.gcs_dir, 'venv.pex')}",
                    f"gsutil cp {SCRIPT_DIR / 'script.py'} {os.path.join(args.gcs_dir, 'script.py')}",
                ]
            ),
            shell=True,
            check=True,
        )


if __name__ == "__main__":
    main()
