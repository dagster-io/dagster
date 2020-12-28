from ..defines import SupportedPython
from ..step_builder import StepBuilder


def next_docs_build_tests():
    return [
        StepBuilder("next docs build tests")
        .run(
            "pip install -e python_modules/automation",
            "pip install -r docs-requirements.txt -qqq",
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "cd docs",
            "make NODE_ENV=production VERSION=master full_docs_build",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("next docs tests")
        .run(
            "pip install -e python_modules/automation",
            "pip install -r docs-requirements.txt -qqq",
            "pip install -r python_modules/dagster/dev-requirements.txt -qqq",
            "cd docs",
            "make buildnext",
            "cd next",
            "yarn test",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        StepBuilder("documentation coverage")
        .run(
            "make install_dev_python_modules",
            "pip install -e python_modules/automation",
            "pip install -r docs-requirements.txt -qqq",
            "cd docs",
            "make updateindex",
            "pytest -vv test_doc_build.py",
            "git diff --exit-code",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
    ]
