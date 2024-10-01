# this script can be used to pack and upload a python .pex file to an s3 bucket
# requires docker and AWS CLI

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent

REQUIREMENTS_TXT = SCRIPT_DIR / "requirements.txt"
DAGSTER_DIR = Path(*SCRIPT_DIR.parts[: SCRIPT_DIR.parts.index("examples")])

DAGSTER_PIPES_DIR = DAGSTER_DIR / "python_modules/dagster-pipes"

parser = argparse.ArgumentParser(description="Upload a python virtualenv to an s3 path")
parser.add_argument(
    "--python", type=str, help="python version to use", default="3.9.16"
)
parser.add_argument(
    "--s3-dir", type=str, help="s3 directory to copy files into", required=True
)


def main():
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as temp_dir:
        os.chdir(temp_dir)
        subprocess.run(
            " && \\\n".join(
                [
                    f"DOCKER_BUILDKIT=1 docker build --output type=local,dest=./output -f {SCRIPT_DIR}/Dockerfile .",
                    f"aws s3 cp ./output/venv.pex {os.path.join(args.s3_dir, 'venv.pex')}",
                    f"aws s3 cp {SCRIPT_DIR / 'script.py'} {os.path.join(args.s3_dir, 'script.py')}",
                ]
            ),
            shell=True,
            check=True,
        )


if __name__ == "__main__":
    main()
