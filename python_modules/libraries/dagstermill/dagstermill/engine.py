import nbformat
from nbconvert.preprocessors.execute import CellExecutionError
from papermill.engines import NBConvertEngine
from papermill.log import logger
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
            source=("import dagstermill as __dm_dagstermill\n" "__dm_dagstermill._teardown()\n")
        )
        new_cell.metadata["tags"] = ["injected-teardown"]
        new_cell.metadata["papermill"] = {}
        index = len(nb_man.nb.cells)
        nb_man.nb.cells = nb_man.nb.cells + [new_cell]

        # Calqued from PapermillExecutePreprocessor.papermill_process
        try:
            nb_man.cell_start(new_cell, index)
            nb_man.nb.cells[index], _ = self.preprocess_cell(new_cell, None, index)
        except CellExecutionError as ex:  # pragma: nocover
            nb_man.cell_exception(nb_man.nb.cells[index], cell_index=index, exception=ex)
        finally:
            nb_man.cell_complete(nb_man.nb.cells[index], cell_index=index)

        return nb_man.nb, resources


class DagstermillNBConvertEngine(NBConvertEngine):
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
        # Nicely handle preprocessor arguments prioritizing values set by engine
        preprocessor = DagstermillExecutePreprocessor(
            timeout=execution_timeout if execution_timeout else kwargs.get("timeout"),
            startup_timeout=start_timeout,
            kernel_name=kernel_name,
            log=logger,
        )

        preprocessor.log_output = log_output  # pylint:disable = attribute-defined-outside-init
        preprocessor.preprocess(nb_man, kwargs)
