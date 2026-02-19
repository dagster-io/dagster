from collections.abc import Callable, Sequence

from buildkite_shared.step_builders.step_builder import StepConfiguration


def transform_steps(
    steps: Sequence[StepConfiguration],
    transform_fn: Callable[[StepConfiguration], None],
) -> Sequence[StepConfiguration]:
    """Apply a transform function to all steps recursively.

    Recursively handles grouped steps. Mutates the steps in place.

    Args:
        steps: List of step dictionaries (StepConfiguration) to modify.
        transform_fn: Function that takes a step and mutates it in place.

    Returns:
        The same steps sequence (for chaining).
    """
    for step in steps:
        transform_fn(step)
        # Handle grouped steps
        if "steps" in step:
            transform_steps(step["steps"], transform_fn)
    return steps


def prefix_commands(steps: Sequence[StepConfiguration], prefix: str) -> Sequence[StepConfiguration]:
    """Prefix all commands in steps with a command.

    Recursively handles grouped steps. Mutates the steps in place.

    Args:
        steps: List of step dictionaries (StepConfiguration) to modify.
        prefix: Command to prepend to each step's commands list.
    """

    def add_prefix(step: StepConfiguration) -> None:
        if "commands" in step:
            step["commands"] = [prefix, *step["commands"]]

    return transform_steps(steps, add_prefix)


def set_step_env_var(
    steps: Sequence[StepConfiguration], key: str, value: str
) -> Sequence[StepConfiguration]:
    """Set an environment variable on all steps.

    Recursively handles grouped steps. Mutates the steps in place.

    Args:
        steps: List of step dictionaries (StepConfiguration) to modify.
        key: Environment variable name.
        value: Environment variable value.
    """

    def add_env_var(step: StepConfiguration) -> None:
        # Only set env on command steps (those with "commands"), not on groups
        if "commands" in step:
            if "env" not in step:
                step["env"] = {}
            step["env"][key] = value

    return transform_steps(steps, add_env_var)
