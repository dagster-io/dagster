import os
import sys

import yaml
from defines import SupportedPython
from step_builder import StepBuilder

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_PATH)

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
            # Reset nightly branch
            'git push --delete origin nightly',
            'git checkout -b nightly',
            'git push --set-upstream origin nightly',
            # Create ~/.pypirc
            '.buildkite/scripts/pypi.sh',
            # Publish
            'export PYTHONDONTWRITEBYTECODE=1',
            'pip install -e python_modules/automation',
            'dagster-release publish --nightly --autoclean',
        )
        .build(),
    ]
    print(yaml.dump({"env": {}, "steps": steps}, default_flow_style=False))
