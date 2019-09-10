import os
import sys

import yaml
from defines import SupportedPython, SupportedPythons
from step_builder import BuildkiteQueue, StepBuilder

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_PATH)


def publish_docker_images():
    # e.g. 27, 35, 36, 37
    python_versions = [''.join(py_version[0].split('.')[:2]) for py_version in SupportedPythons]

    return [
        StepBuilder("docker image %s" % version)
        .run(
            "pip install awscli",
            "aws s3 cp s3://${BUILDKITE_SECRETS_BUCKET}/dockerhub-creds /tmp/dockerhub-creds",
            "cat /tmp/dockerhub-creds | docker login --username elementldevtools --password-stdin",
            "pushd /workdir/.buildkite/images/",
            "make build-public-{version}".format(version=version),
            "make push-public-{version}".format(version=version),
        )
        .on_integration_image(SupportedPython.V3_7)
        .on_queue(BuildkiteQueue.DOCKER)
        .with_timeout(30)
        .build()
        for version in python_versions
    ]


if __name__ == "__main__":
    steps = [
        StepBuilder('publish nightlies')
        .on_integration_image(
            SupportedPython.V3_7, ['SLACK_RELEASE_BOT_TOKEN', 'PYPI_USERNAME', 'PYPI_PASSWORD']
        )
        .run(
            # Configure git
            'git config --global user.email "$GITHUB_EMAIL"',
            'git config --global user.name "$GITHUB_NAME"',
            # Merge Master
            'git fetch --all',
            'git branch -D master',
            'git checkout --track origin/master',
            'git reset --hard origin/master',
            'git checkout --track origin/nightly',
            'git checkout nightly',
            'git reset --hard origin/nightly',
            'GIT_MERGE_AUTOEDIT=no git merge --strategy recursive --strategy-option theirs master',
            'git push',
            # Install reqs
            'pip install -r bin/requirements.txt',
            # Create ~/.pypirc
            '.buildkite/scripts/pypi.sh',
            # Publish
            'python bin/publish.py publish --nightly --autoclean',
        )
        .build(),
        StepBuilder('clean phabricator tags')
        .run('git tag | grep phabricator | xargs git push -d origin')
        .build(),
    ]

print(yaml.dump({"env": {}, "steps": publish_docker_images() + steps}, default_flow_style=False))
