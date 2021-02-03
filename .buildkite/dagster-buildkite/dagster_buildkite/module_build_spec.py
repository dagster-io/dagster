from collections import namedtuple

from .defines import TOX_MAP, SupportedPython, SupportedPythons
from .step_builder import StepBuilder

MYPY_EXCLUDES = [
    "python_modules/dagit",
    "python_modules/automation",
    "python_modules/dagster-graphql",
    "python_modules/libraries/dagster-databricks",
    "python_modules/libraries/dagster-dbt",
    "python_modules/libraries/dagster-docker",
    "python_modules/libraries/lakehouse",
    "examples/docs_snippets",
]


class ModuleBuildSpec(
    namedtuple(
        "_ModuleBuildSpec",
        "directory env_vars supported_pythons extra_cmds_fn depends_on_fn tox_file "
        "tox_env_suffixes buildkite_label retries upload_coverage",
    )
):
    """Main spec for testing Dagster Python modules using tox.

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
        tox_file (str, optional): The tox file to use. Defaults to None (uses the default tox.ini
            file).
        tox_env_suffixes: (List[str], optional): List of additional tox env suffixes to provide
            when invoking tox. When provided, a separate test run will be invoked per
            env x env_suffix string. For example, given Python tox version py38, the
            tox_env_suffixes ["-a", "-b"] will result in running "tox -e py38-a" and "tox -e py38-b"
            as two build steps. Defaults to None.
        buildkite_label (str, optional): Optional label to override what's shown in Buildkite.
            Defaults to None (uses the package name as the label).
        retries (int, optional): Whether to retry these tests on failure
        upload_coverage (bool, optional): Whether to copy coverage artifacts. Enabled by default.

    Returns:
        List[dict]: List of test steps
    """

    def __new__(
        cls,
        directory,
        env_vars=None,
        supported_pythons=None,
        extra_cmds_fn=None,
        depends_on_fn=None,
        tox_file=None,
        tox_env_suffixes=None,
        buildkite_label=None,
        retries=None,
        upload_coverage=True,
    ):
        return super(ModuleBuildSpec, cls).__new__(
            cls,
            directory,
            env_vars or [],
            supported_pythons or SupportedPythons,
            extra_cmds_fn,
            depends_on_fn,
            tox_file,
            tox_env_suffixes,
            buildkite_label,
            retries,
            upload_coverage,
        )

    def get_tox_build_steps(self):
        package = self.buildkite_label or self.directory.split("/")[-1]
        tests = []

        tox_env_suffixes = self.tox_env_suffixes or [""]

        for version in self.supported_pythons:
            for tox_env_suffix in tox_env_suffixes:
                label = package + tox_env_suffix

                extra_cmds = self.extra_cmds_fn(version) if self.extra_cmds_fn else []

                # See: https://github.com/dagster-io/dagster/issues/2512
                tox_file = "-c %s " % self.tox_file if self.tox_file else ""
                tox_cmd = f"tox -vv {tox_file}-e {TOX_MAP[version]}{tox_env_suffix}"

                cmds = extra_cmds + [f"cd {self.directory}", tox_cmd]

                if self.upload_coverage:
                    coverage = f".coverage.{label}.{version}.$BUILDKITE_BUILD_ID"
                    cmds += [
                        f"mv .coverage {coverage}",
                        f"buildkite-agent artifact upload {coverage}",
                    ]

                step = (
                    StepBuilder(f":pytest: {label} {version[:3]}")
                    .run(*cmds)
                    .on_integration_image(version, self.env_vars or [])
                )

                if self.retries:
                    step = step.with_retry(self.retries)

                if self.depends_on_fn:
                    step = step.depends_on(self.depends_on_fn(version))

                tests.append(step.build())

        # We expect the tox file to define a pylint testenv, and we'll construct a separate
        # buildkite build step for the pylint testenv.
        tests.append(
            StepBuilder(f":lint-roller: {package}")
            .run(f"cd {self.directory}", "tox -vv -e pylint")
            .on_integration_image(SupportedPython.V3_7)
            .build()
        )

        # We expect the tox file to define a mypy testenv, and we'll construct a separate
        # buildkite build step for the mypy testenv.
        if self.directory not in MYPY_EXCLUDES:
            tests.append(
                StepBuilder(f":mypy: {package}")
                .run(
                    "pip install mypy==0.790",
                    f"mypy --config-file mypy/config {self.directory}",
                )
                .on_integration_image(SupportedPython.V3_7)
                .build()
            )

        return tests
