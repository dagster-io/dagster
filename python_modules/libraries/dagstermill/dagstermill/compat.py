import papermill
from packaging.version import Version, parse
from papermill.exceptions import PapermillExecutionError


def is_papermill_2():
    version = parse(papermill.__version__)
    # satisfies typechecker that might think version is a LegacyVersion
    assert isinstance(version, Version)
    return version.major == 2


if is_papermill_2():
    from nbclient.exceptions import CellExecutionError

    ExecutionError = (PapermillExecutionError, CellExecutionError)

else:
    ExecutionError = PapermillExecutionError
