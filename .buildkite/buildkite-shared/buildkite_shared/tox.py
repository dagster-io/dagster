from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

from buildkite_shared.python_version import AvailablePythonVersion
from buildkite_shared.step_builders.command_step_builder import (
    BuildkiteQueue,
    CommandStepBuilder,
    CommandStepConfiguration,
    ResourceRequests,
    StepBuilderMutator,
)

ToxImage = Literal["test", "integration", "integration_slim"]


def build_tox_step(
    directory: str | Path,
    tox_env: str,
    *,
    key: str,
    label_emojis: list[str],
    timeout_in_minutes: int | None = None,
    tox_file: str | None = None,
    extra_commands_pre: list[str] | None = None,
    extra_commands_post: list[str] | None = None,
    env: list[str] | None = None,
    image: ToxImage = "test",
    python_version: AvailablePythonVersion | None = None,
    ecr_account_ids: list[str | None] | None = None,
    queue: BuildkiteQueue | None = None,
    depends_on: str | Sequence[str] | None = None,
    skip_reason: str | None = None,
    pytest_args: list[str] | None = None,
    concurrency: int | None = None,
    concurrency_group: str | None = None,
    resources: ResourceRequests | None = None,
    soft_fail: bool = False,
    with_docker: bool = True,
    ecr_passthru: bool = False,
    section_header: str | None = None,
    command_wrapper: Callable[[str], str] | None = None,
    mutator: StepBuilderMutator | None = None,
) -> CommandStepConfiguration:
    """Build a single Buildkite command step that runs `tox -e <tox_env>` in `directory`.

    The caller is responsible for cross-products over python versions, factors, and
    splits — this factory returns exactly one step per call.

    image controls which CommandStepBuilder image method is invoked:
      - "test":             .on_test_image(python_version.value, env=env)
      - "integration":      .on_integration_image(env=env, ecr_account_ids=ecr_account_ids)
      - "integration_slim": .on_integration_slim_image(env=env)

    command_wrapper, if provided, wraps the rendered `tox ...` command string before it
    is added to .run() — e.g. for buildevents/Honeycomb instrumentation.

    mutator, if provided, receives the CommandStepBuilder right before .build() — used as
    an escape hatch for per-step modifications that aren't worth a new kwarg.
    """
    tox_command_parts = filter(
        None,
        [
            "tox",
            f"-c {tox_file} " if tox_file else None,
            "-vv",
            "-e",
            tox_env,
            "--" if pytest_args else None,
            " ".join(pytest_args) if pytest_args else None,
        ],
    )
    tox_command = " ".join(tox_command_parts)
    if command_wrapper is not None:
        tox_command = command_wrapper(tox_command)

    commands: list[str] = [
        *(extra_commands_pre or []),
        f"cd {directory}",
        # Caller is responsible for shell-quoting section_header if it contains
        # ANSI escapes or other special chars (OSS uses make_buildkite_section_header
        # + shlex.quote; internal passes a plain "--- foo" string).
        *([f"echo -e {section_header}"] if section_header else []),
        tox_command,
        *(extra_commands_post or []),
    ]

    builder = CommandStepBuilder(key, label_emojis)
    builder.with_timeout(timeout_in_minutes)

    if image == "test":
        resolved_version = python_version or AvailablePythonVersion.get_default()
        builder.on_test_image(resolved_version.value, env=env or [])
    elif image == "integration":
        integration_kwargs: dict[str, object] = {"env": env or []}
        if ecr_account_ids is not None:
            integration_kwargs["ecr_account_ids"] = ecr_account_ids
        builder.on_integration_image(**integration_kwargs)  # type: ignore[arg-type]
    elif image == "integration_slim":
        builder.on_integration_slim_image(env=env or [])

    builder.run(*commands)
    builder.depends_on(depends_on)
    builder.skip(skip_reason)

    if queue is not None:
        builder.on_queue(queue)
    if resources is not None:
        builder.resources(resources)
    if with_docker:
        builder.with_docker()
    if ecr_passthru:
        builder.with_ecr_passthru()

    if concurrency is not None or concurrency_group is not None:
        if concurrency is None or concurrency_group is None:
            raise ValueError("Both 'concurrency' and 'concurrency_group' must be set together")
        builder.concurrency(concurrency)
        builder.concurrency_group(concurrency_group)

    if soft_fail:
        builder.soft_fail()

    if mutator is not None:
        builder = mutator(builder)

    return builder.build()
