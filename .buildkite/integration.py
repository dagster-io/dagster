import os
import sys

import yaml
from defines import SupportedPython, SupportedPythons
from step_builder import BuildkiteQueue, StepBuilder, wait_step

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)


def image_input_step():
    return {
        'input': 'Integration Image Version',
        'fields': [
            {
                'text': 'Image Version String',
                'hint': 'The version of integration images to publish (e.g. v5, v6, etc.)',
                'key': 'integration-image-version',
            }
        ],
    }


def publish_integration_images():
    return [
        StepBuilder("Integration Image %s" % python_version)
        .run(
            # See: https://buildkite.com/docs/pipelines/build-meta-data
            "export IMAGE_VERSION=$$(buildkite-agent meta-data get \"integration-image-version\")",
            "pip install awscli",
            "aws ecr get-login --no-include-email --region us-west-1 | sh",
            "cd /workdir/.buildkite/images/",
            "make VERSION=\"$$IMAGE_VERSION\" build-integration-{python_version}".format(
                python_version=''.join(python_version.split('.')[:2])
            ),
            "make VERSION=\"$$IMAGE_VERSION\" push-integration-{python_version}".format(
                python_version=python_version
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
        for python_version in SupportedPythons + [SupportedPython.V3_8]
    ]


if __name__ == "__main__":
    print(
        yaml.dump(
            {"steps": [image_input_step(), wait_step()] + publish_integration_images()},
            default_flow_style=False,
        )
    )
