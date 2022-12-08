import papermill
from packaging.version import parse
from papermill.exceptions import PapermillExecutionError


def is_papermill_2():
    version = parse(papermill.__version__)
    return version.major == 2


if is_papermill_2():
    from nbclient.exceptions import CellExecutionError  # pylint: disable=import-error

    ExecutionError = (PapermillExecutionError, CellExecutionError)

else:
    ExecutionError = PapermillExecutionError
