from typing import List

from ..defines import SupportedPython
from ..step_builder import StepBuilder


def docs_steps() -> List[dict]:
    return [
        # If this test is failing because you may have either:
        #   (1) Updated the code that is referenced by a literalinclude in the documentation
        #   (2) Directly modified the inline snapshot of a literalinclude instead of updating
        #       the underlying code that the literalinclude is pointing to.
        # To fix this, run 'make snapshot' in the /docs directory to update the snapshots.
        # Be sure to check the diff to make sure the literalincludes are as you expect them."
        StepBuilder("docs code snapshots")
        .run("pushd docs; make docs_dev_install; make snapshot", "git diff --exit-code")
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        # Make sure the docs site can build end-to-end.
        StepBuilder("docs next")
        .run(
            "pushd docs/next",
            "yarn",
            "yarn test",
            "yarn build-master",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        # Make sure the docs site can build end-to-end.
        StepBuilder("crag docs next")
        .run(
            "pushd docs/next",
            "yarn",
            "yarn crag-test",
            "yarn crag-build-master",
        )
        .on_integration_image(SupportedPython.V3_7)
        .build(),
        # TODO: Yuhan to fix
        # StepBuilder("docs sphinx json build")
        # .run(
        #     "pip install -e python_modules/automation",
        #     "pip install -r docs-requirements.txt -qqq",
        #     "pushd docs; make build",
        #     "git diff --exit-code",
        # )
        # .on_integration_image(SupportedPython.V3_7)
        # .build(),
    ]
