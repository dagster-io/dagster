import os

from click import UsageError
from dagster import check
from dagster.core.definitions.reconstructable import ReconstructableRepository


def _cli_load_invariant(condition, msg=None):
    msg = (
        msg
        or "Invalid set of CLI arguments for loading repository/pipeline. See --help for details."
    )
    if not condition:
        raise UsageError(msg)


def recon_repo_for_cli_args(kwargs):
    """Builds a ReconstructableRepository for CLI arguments, which can be any of the combinations
    for repo loading above.
    """
    check.dict_param(kwargs, "kwargs")
    _cli_load_invariant(kwargs.get("pipeline_name") is None)

    if kwargs.get("workspace"):
        check.not_implemented("Workspace not supported yet in this cli command")

    elif kwargs.get("module_name") and kwargs.get("fn_name"):
        _cli_load_invariant(kwargs.get("repository_yaml") is None)
        _cli_load_invariant(kwargs.get("python_file") is None)
        return ReconstructableRepository.for_module(kwargs["module_name"], kwargs["fn_name"])

    elif kwargs.get("python_file") and kwargs.get("fn_name"):
        _cli_load_invariant(kwargs.get("repository_yaml") is None)
        _cli_load_invariant(kwargs.get("module_name") is None)
        return ReconstructableRepository.for_file(
            os.path.abspath(kwargs["python_file"]),
            kwargs["fn_name"],
            kwargs.get("working_directory") if kwargs.get("working_directory") else os.getcwd(),
        )
    else:
        _cli_load_invariant(False)
