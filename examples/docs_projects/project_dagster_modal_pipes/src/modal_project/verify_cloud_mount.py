"""Simple script to verify Modal cloud mount.

Example Usage

    modal run modal_project.verify_cloud_mount

"""

import os
import subprocess

import modal

app = modal.App(
    image=modal.Image.debian_slim(python_version="3.10").pip_install(
        "python-dotenv",
    )
)

from dotenv import load_dotenv

load_dotenv()

CLOUDFLARE_R2_API = os.environ.get("CLOUDFLARE_R2_API")
CLOUDFLARE_R2_ACCESS_KEY_ID = os.environ.get("CLOUDFLARE_R2_ACCESS_KEY_ID")
CLOUDFLARE_R2_SECRET_ACCESS_KEY = os.environ.get("CLOUDFLARE_R2_SECRET_ACCESS_KEY")


# NOTE: environment variables are loaded on the host machine via `load_dotenv` as the
# `bucket_endpoint_url` is used outside of the scope of the `secret` parameter. Otherwise, the
# `modal.Secret.from_dotenv()` method would be used.
cloud_bucket_mount = modal.CloudBucketMount(
    "dagster-modal-demo",
    bucket_endpoint_url=CLOUDFLARE_R2_API,
    secret=modal.Secret.from_dict(
        {
            "AWS_ACCESS_KEY_ID": CLOUDFLARE_R2_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": CLOUDFLARE_R2_SECRET_ACCESS_KEY,
            "AWS_REGION": "auto",
        }
    ),
    read_only=True,
)


@app.function(
    volumes={"/mount": cloud_bucket_mount},
)
def f():
    subprocess.run(["ls", "/mount/dagster-modal-demo/data"], check=True)
