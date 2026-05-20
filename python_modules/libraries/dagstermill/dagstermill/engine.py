import nbformat
from papermill.clientwrap import PapermillNotebookClient
from papermill.engines import NBClientEngine
from papermill.log import logger
from papermill.utils import merge_kwargs, remove_args

from dagstermill.compat import ExecutionError


class DagstermillNotebookClient(PapermillNotebookClient):
    def papermill_execute_cells(self):
        try:
            for index, cell in enumerate(self.nb.cells):
                try:
                    self.nb_man.cell_start(cell, index)
                    self.execute_cell(cell, index)
                except ExecutionError as ex:
                    self.nb_man.cell_exception(self.nb.cells[index], cell_index=index, exception=ex)
                    break
                finally:
                    self.nb_man.cell_complete(self.nb.cells[index], cell_index=index)
        finally:
            new_cell = nbformat.v4.new_code_cell(
                source="import dagstermill as __dm_dagstermill\n__dm_dagstermill._teardown()\n"
            )
            new_cell.metadata["tags"] = ["injected-teardown"]
            new_cell.metadata["papermill"] = {
                "exception": None,
                "start_time": None,
                "end_time": None,
                "duration": None,
                "status": self.nb_man.PENDING,
            }
            index = len(self.nb_man.nb.cells)
            self.nb_man.nb.cells = self.nb_man.nb.cells + [new_cell]
            try:
                self.nb_man.cell_start(new_cell, index)
                self.execute_cell(new_cell, index)
            except ExecutionError as ex:
                self.nb_man.cell_exception(self.nb.cells[index], cell_index=index, exception=ex)
            finally:
                self.nb_man.cell_complete(self.nb.cells[index], cell_index=index)


class DagstermillEngine(NBClientEngine):
    @classmethod
    def execute_managed_notebook(
        cls,
        nb_man,
        kernel_name,
        log_output=False,
        stdout_file=None,
        stderr_file=None,
        start_timeout=120,
        execution_timeout=None,
        **kwargs,
    ):
        # Exclude parameters that named differently downstream
        safe_kwargs = remove_args(["timeout", "startup_timeout", "input_path"], **kwargs)

        # Nicely handle preprocessor arguments prioritizing values set by engine
        final_kwargs = merge_kwargs(
            safe_kwargs,
            timeout=execution_timeout if execution_timeout else kwargs.get("timeout"),
            startup_timeout=start_timeout,
            kernel_name=kernel_name,
            log=logger,
            log_output=log_output,
            stdout_file=stdout_file,
            stderr_file=stderr_file,
        )
        return DagstermillNotebookClient(nb_man, **final_kwargs).execute()
