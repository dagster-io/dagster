import datetime
import os
import sys

import yaml
from defines import INTEGRATION_BASE_VERSION, SupportedPythons
from step_builder import BuildkiteQueue, StepBuilder

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


def publish_integration_images():
    publish_date = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H%M%S")

    steps = []
    for python_version in SupportedPythons:
        python_image = 'buildkite-integration-base:py{python_version}-{base_image_version}'.format(
            python_version=python_version, base_image_version=INTEGRATION_BASE_VERSION,
        )

        steps.append(
            StepBuilder("Integration Image %s" % python_version)
            .run(
                r"aws s3 cp s3://\${BUILDKITE_SECRETS_BUCKET}/dockerhub-creds /tmp/dockerhub-creds",
                "export DOCKERHUB_PASSWORD=`cat /tmp/dockerhub-creds`",
                "export DOCKERHUB_USERNAME=elementldevtools",
                "aws ecr get-login --no-include-email --region us-west-1 | sh",
                "cd /workdir/.buildkite/images/",
                (
                    'cd /workdir && pip install click==7.1.2 '
                    '-e python_modules/dagster -e python_modules/automation'
                ),
                (
                    'python /workdir/.buildkite/images/integration/image_build.py '
                    '-v {python_version} -i {publish_date} -b {base_image_version}'
                ).format(
                    python_version=python_version,
                    publish_date=publish_date,
                    base_image_version=INTEGRATION_BASE_VERSION,
                ),
                (
                    'python /workdir/.buildkite/images/integration/image_push.py '
                    '-v {python_version} -i {publish_date}'
                ).format(python_version=python_version, publish_date=publish_date,),
            )
            .on_python_image(
                python_image,
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
        )

    return steps


if __name__ == "__main__":
    print(yaml.dump({"steps": publish_integration_images()}, default_flow_style=False,))
