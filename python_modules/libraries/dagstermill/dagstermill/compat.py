import packaging
import papermill
from papermill.exceptions import PapermillExecutionError

IS_PAPERMILL_2 = packaging.version.parse(papermill.__version__).major == 2


if IS_PAPERMILL_2:
    from nbclient.exceptions import CellExecutionError  # pylint: disable=import-error

    ExecutionError = (PapermillExecutionError, CellExecutionError)

else:
    ExecutionError = PapermillExecutionError
