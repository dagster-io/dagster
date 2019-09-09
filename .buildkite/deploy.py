import os
import sys

import yaml
from defines import SupportedPython
from step_builder import BuildkiteQueue, StepBuilder

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


def deploy_scala():
    # GCP tests need appropriate credentials
    creds_local_file = "/tmp/gcp-key-elementl-dev.json"
    version = SupportedPython.V3_7

    return (
        StepBuilder("scala deploy")
        .run(
            "pip install awscli",
            "pip install --upgrade google-cloud-storage",
            r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/gcp-key-elementl-dev.json "
            + creds_local_file,
            "export GOOGLE_APPLICATION_CREDENTIALS=" + creds_local_file,
            "pushd scala_modules",
            "make deploy",
        )
        .on_integration_image(
            version,
            [
                'AWS_SECRET_ACCESS_KEY',
                'AWS_ACCESS_KEY_ID',
                'AWS_DEFAULT_REGION',
                'BUILDKITE_SECRETS_BUCKET',
                'GCP_PROJECT_ID',
                'GCP_DEPLOY_BUCKET',
            ],
        )
        .on_queue(BuildkiteQueue.MEDIUM)
        .build()
    )


if __name__ == "__main__":
    print(yaml.dump({"steps": [deploy_scala()]}, default_flow_style=False))
