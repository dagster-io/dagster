import os
import sys
from collections import namedtuple

SCRIPT_PATH = os.path.dirname(os.path.abspath(__file__))

sys.path.append(SCRIPT_PATH)
from defines import SupportedPythons, TOX_MAP  # isort:skip
from step_builder import StepBuilder  # isort:skip


class ModuleBuildSpec(
    namedtuple(
        '_ModuleBuildSpec', 'directory env_vars supported_pythons extra_cmds_fn depends_on_fn'
    )
):
    '''Main spec for testing Dagster Python modules using tox.

    Args:
        directory (str): Python directory to test, relative to the repository root. Should contain a
            tox.ini file.
        env_vars (List[str], optional): Additional environment variables to pass through to the
            test. Make sure you set these in tox.ini also, using ``passenv``! Defaults to None.
        supported_pythons (List[str], optional): Optional overrides for Python versions to test.
            Tests are generated for each version of Python listed here; each test will run in an
            integration test image for that Python version, and ``tox -e <<VERSION>>`` will be
            invoked for the corresponding Python version. Defaults to None (all supported Pythons).
        extra_cmds_fn (Callable[str, List[str]], optional): Optional callable to create more
            commands to run before the main test invocation through tox. Function takes a single
            argument, which is the Python version being invoked, and returns a list of shell
            commands to execute, one invocation per list item. Defaults to None (no additional
            commands).
        depends_on_fn (Callable[str, List[str]], optional): Optional callable to create a
            Buildkite dependency (e.g. on test image build step). Function takes a single
            argument, which is the Python version being invoked, and returns a list of names of
            other Buildkite build steps this build step should depend on. Defaults to None (no
            dependencies).

    Returns:
        List[dict]: List of test steps
    '''

    def __new__(
        cls,
        directory,
        env_vars=None,
        supported_pythons=None,
        extra_cmds_fn=None,
        depends_on_fn=None,
    ):
        return super(ModuleBuildSpec, cls).__new__(
            cls,
            directory,
            env_vars or [],
            supported_pythons or SupportedPythons,
            extra_cmds_fn,
            depends_on_fn,
        )

    def get_tox_build_steps(self):
        label = self.directory.split("/")[-1]
        tests = []

        for version in self.supported_pythons:
            coverage = ".coverage.{label}.{version}.$BUILDKITE_BUILD_ID".format(
                label=label, version=version
            )

            extra_cmds = self.extra_cmds_fn(version) if self.extra_cmds_fn else []

            cmds = extra_cmds + [
                "cd {directory}".format(directory=self.directory),
                # See: https://github.com/dagster-io/dagster/issues/2512
                "tox -vv -e {ver}".format(ver=TOX_MAP[version]),
                "mv .coverage {file}".format(file=coverage),
                "buildkite-agent artifact upload {file}".format(file=coverage),
            ]

            step = (
                StepBuilder("{label} tests ({ver})".format(label=label, ver=TOX_MAP[version]))
                .run(*cmds)
                .on_integration_image(version, self.env_vars or [])
            )

            if self.depends_on_fn:
                step = step.depends_on(self.depends_on_fn(version))

            tests.append(step.build())

        return tests
