import datetime
import os
import sys

import yaml
from defines import SupportedPython, SupportedPythons
from step_builder import BuildkiteQueue, StepBuilder

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


def publish_integration_images():
    python_versions = [
        ''.join(python_version.split('.')[:2]) for python_version in SupportedPythons
    ]
    publish_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")

    return [
        StepBuilder("Integration Image %s" % python_version)
        .run(
            r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/dockerhub-creds /tmp/dockerhub-creds",
            "export DOCKERHUB_PASSWORD=`cat /tmp/dockerhub-creds`",
            "export DOCKERHUB_USERNAME=elementldevtools",
            "aws ecr get-login --no-include-email --region us-west-1 | sh",
            "cd /workdir/.buildkite/images/",
            "make VERSION=\"{publish_date}\" build-integration-{python_version}".format(
                publish_date=publish_date, python_version=python_version
            ),
            "make VERSION=\"{publish_date}\" push-integration-{python_version}".format(
                publish_date=publish_date, python_version=python_version
            ),
        )
        .on_integration_image(
            SupportedPython.V3_7,
            [
                'AWS_ACCOUNT_ID',
                'AWS_ACCESS_KEY_ID',
                'AWS_SECRET_ACCESS_KEY',
                'BUILDKITE_SECRETS_BUCKET',
            ],
        )
        .on_queue(BuildkiteQueue.DOCKER)
        .with_timeout(30)
        .build()
        for python_version in python_versions
    ]


if __name__ == "__main__":
    print(yaml.dump({"steps": publish_integration_images()}, default_flow_style=False,))
