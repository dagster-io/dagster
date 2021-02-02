from typing import List

from ..defines import SupportedPython
from ..step_builder import StepBuilder


def docs_steps() -> List[dict]:
    return [
        StepBuilder("docs validate-libraries")
        .run("pip install -e python_modules/automation", "dagster-docs validate-libraries")
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("docs next build tests")
        .run(
            "pip install -r docs-requirements.txt -qqq",
            "cd docs",
            "make NODE_ENV=production VERSION=master full_docs_build",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("docs next tests")
        .run(
            "pip install -r docs-requirements.txt -qqq",
            "cd docs",
            "make buildnext",
            "cd next",
            "yarn test",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder(":coverage: docs")
        .run(
            "pip install -r docs-requirements.txt -qqq",
            "cd docs",
            "make updateindex",
            "pytest -vv test_doc_build.py",
            "git diff --exit-code",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
