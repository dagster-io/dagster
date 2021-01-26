from typing import List

# from ..defines import SupportedPython
# from ..step_builder import StepBuilder


def docs_steps() -> List[dict]:
    return [
        # TODO: Yuhan to fix
        # StepBuilder("docs sphinx build")
        # .run(
        #     "pip install -e python_modules/automation",
        #     "pip install -r docs-requirements.txt -qqq",
        #     "pushd docs; make build",
        #     "git diff --exit-code",
        # )
        # .on_integration_image(SupportedPython.V3_7)
        # .build(),
    ]
