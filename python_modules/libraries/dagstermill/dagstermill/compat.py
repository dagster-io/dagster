from nbclient.exceptions import CellExecutionError
from papermill.exceptions import PapermillExecutionError

ExecutionError = (PapermillExecutionError, CellExecutionError)
