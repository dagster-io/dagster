from abc import abstractmethod
from collections import defaultdict
from datetime import datetime

import sqlalchemy as db

from dagster import check
from dagster.core.events import DagsterEvent, DagsterEventType
from dagster.core.serdes import deserialize_json_to_dagster_namedtuple, serialize_dagster_namedtuple

from ..pipeline_run import PipelineRun, PipelineRunStatus
from .base import RunStorage
from .schema import RunTagsTable, RunsTable


class SqlRunStorage(RunStorage):  # pylint: disable=no-init
    @abstractmethod
    def connect(self):
        '''Context manager yielding a sqlalchemy.engine.Connection.'''

    def execute(self, query):
        with self.connect() as conn:
            result_proxy = conn.execute(query)
            res = result_proxy.fetchall()
            result_proxy.close()

        return res

    def add_run(self, pipeline_run):
        check.inst_param(pipeline_run, 'pipeline_run', PipelineRun)

        with self.connect() as conn:
            runs_insert = RunsTable.insert().values(  # pylint: disable=no-value-for-parameter
                run_id=pipeline_run.run_id,
                pipeline_name=pipeline_run.pipeline_name,
                status=pipeline_run.status.value,
                run_body=serialize_dagster_namedtuple(pipeline_run),
            )
            conn.execute(runs_insert)
            if pipeline_run.tags and len(pipeline_run.tags) > 0:
                conn.execute(
                    RunTagsTable.insert(),  # pylint: disable=no-value-for-parameter
                    [
                        dict(run_id=pipeline_run.run_id, key=k, value=v)
                        for k, v in pipeline_run.tags.items()
                    ],
                )

        return pipeline_run

    def handle_run_event(self, run_id, event):
        check.str_param(run_id, 'run_id')
        check.inst_param(event, 'event', DagsterEvent)

        lookup = {
            DagsterEventType.PIPELINE_START: PipelineRunStatus.STARTED,
            DagsterEventType.PIPELINE_SUCCESS: PipelineRunStatus.SUCCESS,
            DagsterEventType.PIPELINE_FAILURE: PipelineRunStatus.FAILURE,
        }

        if event.event_type not in lookup:
            return

        run = self.get_run_by_id(run_id)
        if not run:
            # TODO log?
            return

        new_pipeline_status = lookup[event.event_type]

        with self.connect() as conn:
            conn.execute(
                RunsTable.update()  # pylint: disable=no-value-for-parameter
                .where(RunsTable.c.run_id == run_id)
                .values(
                    status=new_pipeline_status.value,
                    run_body=serialize_dagster_namedtuple(run.run_with_status(new_pipeline_status)),
                    update_timestamp=datetime.now(),
                )
            )

    def _rows_to_runs(self, rows):
        return list(map(lambda r: deserialize_json_to_dagster_namedtuple(r[0]), rows))

    def _build_query(self, query, cursor, limit):
        ''' Helper function to deal with cursor/limit pagination args '''

        if cursor:
            cursor_query = db.select([RunsTable.c.id]).where(RunsTable.c.run_id == cursor)
            query = query.where(RunsTable.c.id < cursor_query)

        if limit:
            query = query.limit(limit)

        query = query.order_by(RunsTable.c.id.desc())
        return query

    def all_runs(self, cursor=None, limit=None):
        '''Return all the runs present in the storage.

        Returns:
            List[PipelineRun]: Tuples of run_id, pipeline_run.
        '''
        query = self._build_query(db.select([RunsTable.c.run_body]), cursor, limit)
        rows = self.execute(query)
        return self._rows_to_runs(rows)

    def get_runs_with_pipeline_name(self, pipeline_name, cursor=None, limit=None):
        '''Return all the runs present in the storage for a given pipeline.

        Args:
            pipeline_name (str): The pipeline to index on

        Returns:
            List[PipelineRun]: Tuples of run_id, pipeline_run.
        '''
        check.str_param(pipeline_name, 'pipeline_name')

        base_query = db.select([RunsTable.c.run_body]).where(
            RunsTable.c.pipeline_name == pipeline_name
        )
        query = self._build_query(base_query, cursor, limit)
        rows = self.execute(query)
        return self._rows_to_runs(rows)

    def get_run_count_with_matching_tags(self, tags):
        sub_query = db.select([1]).select_from(
            RunsTable.outerjoin(RunTagsTable, RunsTable.c.run_id == RunTagsTable.c.run_id)
        )

        sub_query = sub_query.where(
            db.or_(
                *(
                    db.and_(RunTagsTable.c.key == key, RunTagsTable.c.value == value)
                    for key, value in tags
                )
            )
        ).group_by(RunsTable.c.run_id)

        if len(tags) > 0:
            sub_query = sub_query.having(db.func.count(RunsTable.c.run_id) == len(tags))

        sub_query = sub_query.alias("matching_runs")

        query = db.select([db.func.count()]).select_from(sub_query)

        rows = self.execute(query)

        count = rows[0][0]
        return count

    def get_runs_with_matching_tags(self, tags, cursor=None, limit=None):
        check.list_param(tags, 'tags', tuple)

        base_query = db.select([RunsTable.c.run_body]).select_from(
            RunsTable.outerjoin(RunTagsTable, RunsTable.c.run_id == RunTagsTable.c.run_id)
        )

        base_query = base_query.where(
            db.or_(
                *(
                    db.and_(RunTagsTable.c.key == key, RunTagsTable.c.value == value)
                    for key, value in tags
                )
            )
        ).group_by(RunsTable.c.run_body, RunsTable.c.id)

        if len(tags) > 0:
            base_query = base_query.having(db.func.count(RunsTable.c.run_id) == len(tags))

        query = self._build_query(base_query, cursor, limit)

        rows = self.execute(query)

        return self._rows_to_runs(rows)

    def get_runs_with_status(self, run_status, cursor=None, limit=None):
        check.inst_param(run_status, 'run_status', PipelineRunStatus)

        base_query = db.select([RunsTable.c.run_body]).where(RunsTable.c.status == run_status.value)
        query = self._build_query(base_query, cursor, limit)
        rows = self.execute(query)

        return self._rows_to_runs(rows)

    def get_run_by_id(self, run_id):
        '''Get a run by its id.

        Args:
            run_id (str): The id of the run

        Returns:
            Optional[PipelineRun]
        '''
        check.str_param(run_id, 'run_id')

        query = db.select([RunsTable.c.run_body]).where(RunsTable.c.run_id == run_id)
        rows = self.execute(query)
        return deserialize_json_to_dagster_namedtuple(rows[0][0]) if len(rows) else None

    def get_run_tags(self):
        result = defaultdict(set)
        query = db.select([RunTagsTable.c.key, RunTagsTable.c.value]).distinct(RunTagsTable.c.value)
        rows = self.execute(query)
        for r in rows:
            result[r[0]].add(r[1])
        return sorted(list([(k, v) for k, v in result.items()]), key=lambda x: x[0])

    def has_run(self, run_id):
        check.str_param(run_id, 'run_id')
        return bool(self.get_run_by_id(run_id))

    def delete_run(self, run_id):
        check.str_param(run_id, 'run_id')
        query = db.delete(RunsTable).where(RunsTable.c.run_id == run_id)
        with self.connect() as conn:
            conn.execute(query)

    def wipe(self):
        '''Clears the run storage.'''
        with self.connect() as conn:
            # https://stackoverflow.com/a/54386260/324449
            conn.execute(RunsTable.delete())  # pylint: disable=no-value-for-parameter
            conn.execute(RunTagsTable.delete())  # pylint: disable=no-value-for-parameter
