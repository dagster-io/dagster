import argparse
import inspect
import json
import sys
from typing import List, Mapping, Tuple

from dagster_external.context import ExternalExecutionContext, init_dagster_external
from dagster_external.params import ExternalExecutionParams, get_external_execution_params
from dagster_external.protocol import ExternalExecutionIOMode
from dagster_external.util import DagsterExternalError


def main() -> None:
    command, params = parse_args(sys.argv)
    validate_args(command, params)
    run_command(command, params)


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Communicate with the dagster orchestration process"
    )
    parser.add_argument("command", type=str, help="Command to run")
    parser.add_argument("params", type=str, nargs="*", help="Arguments to pass to command")
    return parser


def parse_args(argv: List[str]) -> Tuple[str, Mapping[str, str]]:
    parser = get_parser()
    args = argv[1:]

    # `--` is necessary to allow arbitrary --key=val style args to be slurped
    # up as positional args.
    if len(args) > 1 and args[1] != "--":
        args.insert(1, "--")
    args = parser.parse_args(args)

    command = args.command.replace("-", "_")
    param_pairs = [arg_str.split("=", 1) for arg_str in args.params]
    params = {key.lstrip("-").replace("-", "_"): value for key, value in param_pairs}
    return command, params


def validate_args(command: str, params: Mapping[str, str]) -> None:
    if command == "get_context":
        return
    elif not (
        hasattr(ExternalExecutionContext, command)
        and callable(getattr(ExternalExecutionContext, command))
    ):
        raise DagsterExternalError(f"Unknown command `{command}`.")
    method = getattr(ExternalExecutionContext, command)

    sig = inspect.signature(method)
    for param in params.keys():
        if param not in sig.parameters:
            raise DagsterExternalError(
                f"Passed unknown parameter `{param}` for command `{command}`."
            )


def validate_env_params(env_params: ExternalExecutionParams) -> None:
    if env_params.input_mode != ExternalExecutionIOMode.file:
        raise DagsterExternalError(
            "When using the `dagster-external` CLI, `input_mode` must be `temp_file`."
        )


def run_command(command: str, cli_params: Mapping[str, str]) -> None:
    context = init_dagster_external()
    env_params = get_external_execution_params()
    validate_env_params(env_params)
    if command == "get_context":
        json.dump(context.to_dict(), sys.stdout)
    elif command == "get_extra":
        json.dump(context.get_extra(**cli_params), sys.stdout)
    else:
        method = getattr(context, command)
        method(**cli_params)


if __name__ == "__main__":
    main()
