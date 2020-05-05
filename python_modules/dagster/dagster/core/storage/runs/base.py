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

        If a run already exists with the same ID, raise DagsterRunAlreadyExists
        If the run's snapshot ID does not exist raise DagsterSnapshotDoesNotExist

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
            filter (Optional[PipelineRunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        '''

    @abstractmethod
    def get_runs_count(self, filters=None):
        '''Return the number of runs present in the storage that match the given filter

        Args:
            filter (Optional[PipelineRunsFilter]) -- The
                :py:class:`~dagster.core.storage.pipeline_run.PipelineRunFilter` by which to filter
                runs
            cursor (Optional[str]): Starting cursor (run_id) of range of runs
            limit (Optional[int]): Number of results to get. Defaults to infinite.

        Returns:
            List[PipelineRun]
        '''

    @abstractmethod
    def get_run_group(self, run_id):
        '''Return a group of runs related to the given run, i.e. the runs shared root_run_id with
        the given run, including the root run.

        Args:
            run_id (str): The id of the run

        Returns:
            Tuple[string, List[PipelineRun]]
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
    def has_pipeline_snapshot(self, pipeline_snapshot_id):
        '''Check to see if storage contains a pipeline snapshot.

        Args:
            pipeline_snapshot_id (str): The id of the run.

        Returns:
            bool
        '''

    @abstractmethod
    def add_pipeline_snapshot(self, pipeline_snapshot):
        '''Add a pipeline snapshot to the run store.

        Pipeline snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            pipeline_snapshot (PipelineSnapshot)

        Return:
            str: The pipeline_snapshot_id
        '''

    @abstractmethod
    def get_pipeline_snapshot(self, pipeline_snapshot_id):
        '''Fetch a snapshot by ID

        Args:
            pipeline_snapshot_id (str)

        Returns:
            PipelineSnapshot
        '''

    @abstractmethod
    def has_execution_plan_snapshot(self, execution_plan_snapshot_id):
        '''Check to see if storage contains an execution plan snapshot.

        Args:
            execution_plan_snapshot_id (str): The id of the execution plan.

        Returns:
            bool
        '''

    @abstractmethod
    def add_execution_plan_snapshot(self, execution_plan_snapshot):
        '''Add an execution plan snapshot to the run store.

        Execution plan snapshots are content-addressable, meaning
        that the ID for a snapshot is a hash based on the
        body of the snapshot. This function returns
        that snapshot ID.

        Args:
            execution_plan_snapshot (ExecutionPlanSnapshot)

        Return:
            str: The execution_plan_snapshot_id
        '''

    @abstractmethod
    def get_execution_plan_snapshot(self, execution_plan_snapshot_id):
        '''Fetch a snapshot by ID

        Args:
            execution_plan_snapshot_id (str)

        Returns:
            ExecutionPlanSnapshot
        '''

    @abstractmethod
    def wipe(self):
        '''Clears the run storage.'''

    @abstractmethod
    def delete_run(self, run_id):
        '''Remove a run from storage'''

    def dispose(self):
        '''Explicit lifecycle management.'''
