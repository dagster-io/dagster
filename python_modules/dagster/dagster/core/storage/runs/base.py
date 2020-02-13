from abc import ABCMeta, abstractmethod

import six


class RunStorage(six.with_metaclass(ABCMeta)):
    '''Abstract base class for storing pipeline run history.
    
    Note that run storages using SQL databases as backing stores should implement
    :py:class:`~dagster.core.storage.runs.SqlRunStorage`.

    Users should not directly instantiate concrete subclasses of this class; they are instantiated
    by internal machinery when ``dagit`` and ``dagster-graphql`` load, based on the values in the
    ``dagster.yaml`` file in ``$DAGSTER_HOME``. Configuration of concrete subclasses of this class
    should be done by setting values in that file.    
    '''

    @abstractmethod
    def add_run(self, pipeline_run):
        '''Add a run to storage.

        Args:
            pipeline_run (PipelineRun): The run to add. If this is not a PipelineRun,
        '''

    @abstractmethod
    def handle_run_event(self, run_id, event):
        '''Update run storage in accordance to a pipeline run related DagsterEvent

        Args:
            event (DagsterEvent)

        '''

    @abstractmethod
    def get_runs(self, filters=None, cursor=None, limit=None):
        '''Return all the runs present in the storage that match the given filter

        Args:
            filter (Optional[PipelineRunsFilter]) -- The PipelineRunFilter to filter runs by
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        '''

    @abstractmethod
    def get_runs_count(self, filters=None):
        '''Return the number of runs present in the storage that match the given filter

        Args:
            filter (Optional[PipelineRunsFilter]) -- The PipelineRunFilter to filter runs by
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        '''

    @abstractmethod
    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        '''

    @abstractmethod
    def get_run_tags(self):
        '''Get a list of tag keys and the values that have been associated with them.

        Returns:
            List[Tuple[string, Set[string]]]
        '''

    @abstractmethod
    def has_run(self, run_id):
        '''Check if the storage contains a run.

        Args:
            run_id (str): The id of the run

        Returns:
            bool
        '''

    @abstractmethod
    def wipe(self):
        '''Clears the run storage.'''

    @abstractmethod
    def delete_run(self, run_id):
        '''Remove a run from storage'''

    def dispose(self):
        '''Explicit lifecycle management.'''
