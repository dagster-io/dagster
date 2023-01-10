import nbformat
from papermill.log import logger

from .compat import ExecutionError, is_papermill_2

if is_papermill_2():
    # pylint: disable=import-error,no-name-in-module
    from papermill.clientwrap import PapermillNotebookClient
    from papermill.engines import NBClientEngine  # pylint: disable=import-error
    from papermill.utils import merge_kwargs, remove_args

    class DagstermillNotebookClient(PapermillNotebookClient):
        def papermill_execute_cells(self):
            try:
                for index, cell in enumerate(self.nb.cells):
                    try:
                        self.nb_man.cell_start(cell, index)
                        self.execute_cell(cell, index)
                    except ExecutionError as ex:
                        self.nb_man.cell_exception(
                            self.nb.cells[index], cell_index=index, exception=ex
                        )
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
            start_timeout=60,
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

else:
    from papermill.engines import NBConvertEngine  # pylint: disable=import-error,no-name-in-module

    # pylint: disable=import-error,no-name-in-module
    from papermill.preprocess import PapermillExecutePreprocessor

    class DagstermillExecutePreprocessor(PapermillExecutePreprocessor):
        # We need to finalize dagster resources here (as opposed to, e.g., in the notebook_complete
        # method on the NotebookExecutionManager), because we need to be inside the scope of the
        # nbconvert.preprocessors.ExecutePreprocessor.setup_preprocessor context manager, which tears
        # the kernel down. Note that atexit doesn't seem to work at all in ipython, and hooking into
        # the ipython post_execute event doesn't work in papermill.
        def papermill_process(self, nb_man, resources):
            _, resources = super(DagstermillExecutePreprocessor, self).papermill_process(
                nb_man, resources
            )

            new_cell = nbformat.v4.new_code_cell(
                source="import dagstermill as __dm_dagstermill\n__dm_dagstermill._teardown()\n"
            )
            new_cell.metadata["tags"] = ["injected-teardown"]
            new_cell.metadata["papermill"] = {}
            index = len(nb_man.nb.cells)
            nb_man.nb.cells = nb_man.nb.cells + [new_cell]

            # Calqued from PapermillExecutePreprocessor.papermill_process
            try:
                nb_man.cell_start(new_cell, index)
                nb_man.nb.cells[index], _ = self.preprocess_cell(new_cell, None, index)
            except ExecutionError as ex:  # pragma: nocover
                nb_man.cell_exception(nb_man.nb.cells[index], cell_index=index, exception=ex)
            finally:
                nb_man.cell_complete(nb_man.nb.cells[index], cell_index=index)

            return nb_man.nb, resources

    class DagstermillEngine(NBConvertEngine):  # type: ignore[no-redef]
        @classmethod
        def execute_managed_notebook(
            cls,
            nb_man,
            kernel_name,
            log_output=False,
            stdout_file=None,  # pylint: disable=unused-argument
            stderr_file=None,  # pylint: disable=unused-argument
            start_timeout=60,
            execution_timeout=None,
            **kwargs,
        ):
            # Nicely handle preprocessor arguments prioritizing values set by engine
            preprocessor = DagstermillExecutePreprocessor(
                timeout=execution_timeout if execution_timeout else kwargs.get("timeout"),
                startup_timeout=start_timeout,
                kernel_name=kernel_name,
                log=logger,
            )

            preprocessor.log_output = log_output  # pylint:disable = attribute-defined-outside-init
            preprocessor.preprocess(nb_man, kwargs)
